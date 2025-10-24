#!/usr/bin/env python3

# Copyright (c) 2000-2025, Board of Trustees of Leland Stanford Jr. University
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Command line tool for managing LOCKSS plugin sets and LOCKSS plugin registries.
"""

# Remove in Python 3.11; see https://docs.python.org/3.11/library/exceptions.html#exception-groups
from exceptiongroup import ExceptionGroup

from getpass import getpass
from itertools import chain
from pathlib import Path

from lockss.pybasic.cliutil import BaseCli, StringCommand, COPYRIGHT_DESCRIPTION, LICENSE_DESCRIPTION, VERSION_DESCRIPTION
from lockss.pybasic.fileutil import file_lines, path
from lockss.pybasic.outpututil import OutputFormatOptions
from pydantic.v1 import BaseModel, Field, FilePath
import tabulate
from typing import Optional

from . import __copyright__, __license__, __version__
from .app import Turtles
from .plugin import PluginIdentifier
from .plugin_registry import PluginRegistryLayerIdentifier
from .util import file_or


class PluginBuildingOptions(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) model for the ``--plugin-set``/``-s``,
    ``--plugin-set-catalog``/``-S``, ``--plugin-signing-credentials``/``-c``,
    ``--plugin-signing-password`` options.
    """

    #: The ``--plugin-set``/``-s`` option.
    plugin_set: Optional[list[FilePath]] = Field(aliases=['-s'],
                                                 title='Plugin Sets',
                                                 description=f'(plugin sets) add one or more plugin set definition files to the loaded plugin sets')

    #: The ``--plugin-set-catalog``/``-S`` option.
    plugin_set_catalog: Optional[list[FilePath]] = Field(aliases=['-S'],
                                                         title='Plugin Set Catalogs',
                                                         description=f'(plugin sets) add one or more plugin set catalogs to the loaded plugin set catalogs; if no plugin set catalogs or plugin sets are specified, load {file_or(Turtles.default_plugin_set_catalog_choices())}')

    #: The ``--plugin-signing-credentials``/``-c`` option.
    plugin_signing_credentials: Optional[FilePath] = Field(aliases=['-c'],
                                                           title='Plugin Signing Credentials',
                                                           description=f'(plugin signing credentials) load the plugin signing credentials from the given file, or if none, from {file_or(Turtles.default_plugin_signing_credentials_choices())}')

    #: The ``--plugin-signing-password`` option.
    plugin_signing_password: Optional[str] = Field(title='Plugin Signing Password',
                                                   description='(plugin signing credentials) set the plugin signing password, or if none, prompt interactively')

    def get_plugin_sets(self) -> list[Path]:
        """
        Returns the cumulative plugin set files.

        :return: The cumulative plugin set files (possibly an empty list).
        :rtype: list[Path]
        """
        return [path(p) for p in self.plugin_set or []]

    def get_plugin_set_catalogs(self) -> list[Path]:
        """
        Returns the cumulative plugin set catalog files.

        :return: The cumulative plugin set catalog files if any plugin set files
                 or plugin set catalog files are specified (possibly an empty
                 list), or the first default plugin set catalog file if no
                 plugin set files nor plugin set catalog files are specified.
        :rtype: list[Path]
        :raise FileNotFoundError: If no plugin set files nor plugin set catalog
                                  files are specified, and none of the default
                                  plugin set catalog file choices exist.
        """
        if self.plugin_set or self.plugin_set_catalog:
            return [path(p) for p in self.plugin_set_catalog or []]
        if single := Turtles.select_default_plugin_set_catalog():
            return [single]
        raise FileNotFoundError(file_or(Turtles.default_plugin_set_catalog_choices()))

    def get_plugin_signing_credentials(self) -> Path:
        """
        Returns the plugin signing credentials file.

        :return: The plugin signing credentials file, or the first default
                 plugin signing credentials file if not specified.
        :rtype: Path
        :raise FileNotFoundError: If no plugin signing credentials file is
                                  specified, and none of the default
                                  plugin signing credentials file choices exist.
        """
        if self.plugin_signing_credentials:
            return path(self.plugin_signing_credentials)
        if ret := Turtles.select_default_plugin_signing_credentials():
            return ret
        raise FileNotFoundError(file_or(Turtles.default_plugin_signing_credentials_choices()))


class PluginDeploymentOptions(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) model for the ``--plugin-registry``/``-r``,
    ``--plugin-registry-catalog``/``-R``, ``--plugin-registry-layer``/``-l``,
    ``--plugin-registry-layers``/``-L``, ``--testing``/``-t``,
    ``--production``/``-P`` options.
    """

    #: The ``--plugin-registry``/``-r`` option.
    plugin_registry: Optional[list[FilePath]] = Field(aliases=['-r'],
                                                      title='Plugin Registries',
                                                      description=f'(plugin registry) add one or more plugin registries to the loaded plugin registries')

    #: The ``--plugin-registry-catalog``/``-R`` option.
    plugin_registry_catalog: Optional[list[FilePath]] = Field(aliases=['-R'],
                                                              title='Plugin Registry Catalogs',
                                                              description=f'(plugin registry) add one or more plugin registry catalogs to the loaded plugin registry catalogs; if no plugin registry catalogs or plugin registries are specified, load {file_or(Turtles.default_plugin_registry_catalog_choices())}')

    #: The ``--plugin-registry-layer``/``-l`` option.
    plugin_registry_layer: Optional[list[str]] = Field(aliases=['-l'],
                                                       title='Plugin Registry Layer Identifiers',
                                                       description='(plugin registry layers) add one or more plugin registry layers to the set of plugin registry layers to process')

    #: The ``--plugin-registry-layers``/``-L`` option.
    plugin_registry_layers: Optional[list[FilePath]] = Field(aliases=['-L'],
                                                             title='Files of Plugin Registry Layer Identifiers',
                                                             description='(plugin registry layers) add the plugin registry layers listed in one or more files to the set of plugin registry layers to process')

    #: The ``--testing``/``-t`` option.
    testing: Optional[bool] = Field(False,
                                    aliases=['-t'],
                                    title='Testing Layer',
                                    description='(plugin registry layers) synonym for --plugin-registry-layer testing (i.e. add "testing" to the list of plugin registry layers to process)')

    #: The ``--production``/``-P`` option.
    production: Optional[bool] = Field(False,
                                       aliases=['-p'],
                                       title='Production Layer',
                                       description='(plugin registry layers) synonym for --plugin-registry-layer production (i.e. add "production" to the list of plugin registry layers to process)')

    def get_plugin_registries(self) -> list[Path]:
        """
        Returns the cumulative plugin registry files.

        :return: The cumulative plugin registry files (possibly an empty list).
        :rtype: list[Path]
        """
        return [path(p) for p in self.plugin_registry or []]

    def get_plugin_registry_catalogs(self) -> list[Path]:
        """
        Returns the cumulative plugin registry catalog files.

        :return: The cumulative plugin registry catalog files if any plugin set
                 files or plugin registry catalog files are specified (possibly
                 an empty list), or the first default plugin registry catalog
                 file if no plugin registry files nor plugin registry catalog
                 files are specified.
        :rtype: list[Path]
        :raise FileNotFoundError: If no plugin registry files nor plugin
                                  registry catalog files are specified, and none
                                  of the default plugin registry catalog file
                                  choices exist.
        """
        if self.plugin_registry or self.plugin_registry_catalog:
            return [path(p) for p in self.plugin_registry_catalog or []]
        if single := Turtles.select_default_plugin_registry_catalog():
            return [single]
        raise FileNotFoundError(file_or(Turtles.default_plugin_set_catalog_choices()))

    def get_plugin_registry_layers(self) -> list[PluginRegistryLayerIdentifier]:
        """
        Returns the cumulative list of plugin registry layer identifiers, from
        ``plugin_registry_layer`` and the identifiers in
        ``plugin_registry_layers`` files.

        :return: The cumulative list of plugin registry layer identifiers, from
                ``plugin_registry_layer`` and the identifiers in
                ``plugin_registry_layers`` files.
        :rtype: list[PluginRegistryLayerIdentifier]
        :raise ValueError: If the list of plugin registry layer identifiers is
                           empty.
        """
        ret = [*(self.plugin_registry_layer or []), *chain.from_iterable(file_lines(path(file_path)) for file_path in self.plugin_registry_layers or [])]
        for layer in reversed(['testing', 'production']):
            if getattr(self, layer, False) and layer not in ret:
                ret.insert(0, layer)
        if ret:
            return ret
        raise ValueError('Empty list of plugin registry layers')


class PluginIdentifierOptions(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) models for the
    ``--plugin-identifier``/``-i``, ``--plugin-identifiers``/``-I`` options.
    """

    #: The ``--plugin-identifier``/``-i`` option.
    plugin_identifier: Optional[list[str]] = Field(aliases=['-i'],
                                                   title='Plugin Identifiers',
                                                   description='(plugin identifiers) add one or more plugin identifiers to the set of plugin identifiers to process')

    #: The ``--plugin-identifiers``/``-I`` option.
    plugin_identifiers: Optional[list[FilePath]] = Field(aliases=['-I'],
                                                         title='Files of Plugin Identifiers',
                                                         description='(plugin identifiers) add the plugin identifiers listed in one or more files to the set of plugin identifiers to process')

    def get_plugin_identifiers(self) -> list[PluginIdentifier]:
        """
        Returns the cumulative list of plugin identifiers, from
        ``plugin_identifier`` and the identifiers in ``plugin_identifiers``
         files.

        :return: The cumulative list of plugin identifiers, from
                ``plugin_identifier`` and the identifiers in
                ``plugin_identifiers`` files.
        :rtype: list[PluginIdentifier]
        :raise ValueError: If the list of plugin identifiers is empty.
        """
        ret = [*(self.plugin_identifier or []), *chain.from_iterable(file_lines(path(file_path)) for file_path in self.plugin_identifiers or [])]
        if ret:
            return ret
        raise ValueError('Empty list of plugin identifiers')


class PluginJarOptions(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) model for the ``--plugin-jar``/``-j``,
    ``--plugin-jars``/``-J`` options.
    """

    #: The ``--plugin-jar``/``-j`` option.
    plugin_jar: Optional[list[FilePath]] = Field(aliases=['-j'],
                                                 title='Plugin JARs',
                                                 description='(plugin JARs) add one or more plugin JARs to the set of plugin JARs to process')

    #: The ``--plugin-jars``/``-J`` option.
    plugin_jars: Optional[list[FilePath]] = Field(aliases=['-J'],
                                                  title='Files of Plugin JARs',
                                                  description='(plugin JARs) add the plugin JARs listed in one or more files to the set of plugin JARs to process')

    def get_plugin_jars(self) -> list[Path]:
        """
        Returns the cumulative list of plugin JARs, from ``plugin_jar`` and the
        plugin JARs in ``plugin_jars``
         files.

        :return: The cumulative list of plugin JARs, from ``plugin_jar`` and the
                 plugin JARs in ``plugin_jars`` files.
        :rtype: list[Path]
        :raise ValueError: If the list of plugin JARs is empty.
        """
        ret = [*(self.plugin_jar or []), *chain.from_iterable(file_lines(path(file_path)) for file_path in self.plugin_jars or [])]
        if len(ret):
            return ret
        raise ValueError('Empty list of plugin JARs')


class NonInteractiveOptions(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) model for the ``--non-interactive`` option.
    """

    #: The ``--non-interactive`` option.
    non_interactive: Optional[bool] = Field(False,
                                            title='Non-Interactive',
                                            description='(plugin signing credentials) disallow interactive prompts')


class TurtlesCommand(BaseModel):
    """
    Pydantic-Argparse (Pydantic v1) model for the ``turtles`` command.
    """

    class BuildPluginCommand(OutputFormatOptions, NonInteractiveOptions, PluginBuildingOptions, PluginIdentifierOptions):
        """
        Pydantic-Argparse (Pydantic v1) model for the ``build-plugin`` command.
        """
        pass

    class DeployPluginCommand(OutputFormatOptions, NonInteractiveOptions, PluginDeploymentOptions, PluginJarOptions):
        """
        Pydantic-Argparse (Pydantic v1) model for the ``deploy-plugin`` command.
        """
        pass

    class ReleasePluginCommand(OutputFormatOptions, NonInteractiveOptions, PluginDeploymentOptions, PluginBuildingOptions, PluginIdentifierOptions):
        """
        Pydantic-Argparse (Pydantic v1) model for the ``release-plugin``
        command.
        """
        pass

    #: The ``bp`` synonym for the ``build-plugin`` command.
    bp: Optional[BuildPluginCommand] = Field(description='synonym for: build-plugin')

    #: The ``build-plugin`` command.
    build_plugin: Optional[BuildPluginCommand] = Field(alias='build-plugin',
                                                       description='build plugins')

    #: The ``copyright`` command.
    copyright: Optional[StringCommand.type(__copyright__)] = Field(description=COPYRIGHT_DESCRIPTION)

    #: The ``deploy-plugin`` command.
    deploy_plugin: Optional[DeployPluginCommand] = Field(alias='deploy-plugin',
                                                         description='deploy plugins')

    #: The ``dp`` synonym for the ``deploy-plugin`` command.
    dp: Optional[DeployPluginCommand] = Field(description='synonym for: deploy-plugin')

    #: The ``license`` command.
    license: Optional[StringCommand.type(__license__)] = Field(description=LICENSE_DESCRIPTION)

    #: The ``release-plugin`` command.
    release_plugin: Optional[ReleasePluginCommand] = Field(alias='release-plugin',
                                                           description='release (build and deploy) plugins')

    #: The ``rp`` synonym for the ``release-plugin`` command.
    rp: Optional[ReleasePluginCommand] = Field(description='synonym for: release-plugin')

    #: The ``version`` command.
    version: Optional[StringCommand.type(__version__)] = Field(description=VERSION_DESCRIPTION)


class TurtlesCli(BaseCli[TurtlesCommand]):
    """
    Command line tool for Turtles.
    """

    def __init__(self):
        """
        Constructor.
        """
        super().__init__(model=TurtlesCommand,
                         prog='turtles',
                         description='Tool for managing LOCKSS plugin sets and LOCKSS plugin registries')
        self._app: Turtles = Turtles()

    # def _analyze_registry(self):
    #     # Prerequisites
    #     self.load_settings(self._args.settings or TurtlesCli._select_config_file(TurtlesCli.SETTINGS))
    #     self.load_plugin_registries(self._args.plugin_registries or TurtlesCli._select_config_file(TurtlesCli.PLUGIN_REGISTRIES))
    #     self.load_plugin_sets(self._args.plugin_sets or TurtlesCli._select_config_file(TurtlesCli.PLUGIN_SETS))
    #
    #     #####
    #     title = 'Plugins declared in a plugin registry but not found in any plugin set'
    #     result = list()
    #     headers = ['Plugin registry', 'Plugin identifier']
    #     for plugin_registry in self._plugin_registries:
    #         for plugin_id in plugin_registry.plugin_identifiers():
    #             for plugin_set in self._plugin_sets:
    #                 if plugin_set.has_plugin(plugin_id):
    #                     break
    #             else: # No plugin set matched
    #                 result.append([plugin_registry.id(), plugin_id])
    #     if len(result) > 0:
    #         self._tabulate(title, result, headers)
    #
    #     #####
    #     title = 'Plugins declared in a plugin registry but with missing JARs'
    #     result = list()
    #     headers = ['Plugin registry', 'Plugin registry layer', 'Plugin identifier']
    #     for plugin_registry in self._plugin_registries:
    #         for plugin_id in plugin_registry.plugin_identifiers():
    #             for layer_id in plugin_registry.get_layer_ids():
    #                 if plugin_registry.get_layer(layer_id).get_file_for(plugin_id) is None:
    #                     result.append([plugin_registry.id(), layer_id, plugin_id])
    #     if len(result) > 0:
    #         self._tabulate(title, result, headers)
    #
    #     #####
    #     title = 'Plugin JARs not declared in any plugin registry'
    #     result = list()
    #     headers = ['Plugin registry', 'Plugin registry layer', 'Plugin JAR', 'Plugin identifier']
    #     # Map from layer path to the layers that have that path
    #     pathlayers = dict()
    #     for plugin_registry in self._plugin_registries:
    #         for layer_id in plugin_registry.get_layer_ids():
    #             layer_id = plugin_registry.get_layer(layer_id)
    #             path = layer_id.path()
    #             pathlayers.setdefault(path, list()).append(layer_id)
    #     # Do report, taking care of not processing a path twice if overlapping
    #     visited = set()
    #     for plugin_registry in self._plugin_registries:
    #         for layer_id in plugin_registry.get_layer_ids():
    #             layer_id = plugin_registry.get_layer(layer_id)
    #             if layer_id.path() not in visited:
    #                 visited.add(layer_id.path())
    #                 for jar_path in layer_id.get_jars():
    #                     if jar_path.stat().st_size > 0:
    #                         plugin_id = Plugin.id_from_jar(jar_path)
    #                         if not any([lay.plugin_registry().has_plugin(plugin_id) for lay in pathlayers[layer_id.path()]]):
    #                             result.append([plugin_registry.id(), layer_id, jar_path, plugin_id])
    #     if len(result) > 0:
    #         self._tabulate(title, result, headers)

    def _bp(self,
            command: TurtlesCommand.BuildPluginCommand) -> None:
        """
        Implementation of the ``bp`` command.

        :param command: The command object.
        :type command: TurtlesCommand.BuildPluginCommand
        """
        return self._build_plugin(command)

    def _build_plugin(self,
                      command: TurtlesCommand.BuildPluginCommand) -> None:
        """
        Implementation of the ``build-plugin`` command.

        :param command: The command object.
        :type command: TurtlesCommand.BuildPluginCommand
        """
        errs = []
        for psc in command.get_plugin_set_catalogs():
            try:
                self._app.load_plugin_set_catalogs(psc)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        for ps in command.get_plugin_sets():
            try:
                self._app.load_plugin_sets(ps)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        try:
            self._app.load_plugin_signing_credentials(command.get_plugin_signing_credentials())
        except ValueError as ve:
            errs.append(ve)
        except ExceptionGroup as eg:
            errs.extend(eg.exceptions)
        if errs:
            raise ExceptionGroup(f'Errors while setting up the environment for building plugins', errs)
        self._obtain_plugin_signing_password(command, non_interactive=command.non_interactive)
        # Action
        # ... plugin_id -> (set_id, jar_path, plugin)
        ret = self._app.build_plugin(command.get_plugin_identifiers())
        # Output
        print(tabulate.tabulate([[plugin_id, plugin.get_version(), set_id, jar_path] for plugin_id, (set_id, jar_path, plugin) in ret.items()],
                                headers=['Plugin identifier', 'Plugin version', 'Plugin set', 'Plugin JAR'],
                                tablefmt=command.output_format))

    def _copyright(self,
                   command: StringCommand) -> None:
        """
        Implementation of the ``copyright`` command.

        :param command: The command object.
        :type command: StringCommand
        """
        self._do_string_command(command)

    def _deploy_plugin(self,
                       command: TurtlesCommand.DeployPluginCommand) -> None:
        """
        Implementation of the ``deploy_plugin`` command.

        :param command: The command object.
        :type command: TurtlesCommand.DeployPluginCommand
        """
        errs = []
        for prc in command.get_plugin_registry_catalogs():
            try:
                self._app.load_plugin_registry_catalogs(prc)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        for pr in command.get_plugin_registries():
            try:
                self._app.load_plugin_registries(pr)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        if errs:
            raise ExceptionGroup(f'Errors while setting up the environment for deploying plugins', errs)
        # Action
        # ... (src_path, plugin_id) -> list of (registry_id, layer_id, dst_path, plugin)
        ret = self._app.deploy_plugin(command.get_plugin_jars(),
                                      command.get_plugin_registry_layers(),
                                      interactive=not command.non_interactive)
        # Output
        print(tabulate.tabulate([[src_path, plugin_id, plugin.get_version(), registry_id, layer_id, dst_path] for (src_path, plugin_id), val in ret.items() for registry_id, layer_id, dst_path, plugin in val],
                                headers=['Plugin JAR', 'Plugin identifier', 'Plugin version', 'Plugin registry', 'Plugin registry layer', 'Deployed JAR'],
                                tablefmt=command.output_format))

    def _do_string_command(self,
                           command: StringCommand) -> None:
        """
        Implementation of string commands.

        :param command: The command object.
        :type command: StringCommand
        """
        command()

    def _dp(self,
            command: TurtlesCommand.DeployPluginCommand) -> None:
        """
        Implementation of the ``dp`` command.

        :param command: The command object.
        :type command: TurtlesCommand.DeployPluginCommand
        """
        return self._deploy_plugin(command)

    def _license(self,
                 command: StringCommand) -> None:
        """
        Implementation of the ``license`` command.

        :param command: The command object.
        :type command: StringCommand
        """
        self._do_string_command(command)

    def _obtain_plugin_signing_password(self,
                                        plugin_building_options: PluginBuildingOptions,
                                        non_interactive: bool=False) -> None:
        """
        Ensures the plugin signing password is specified.

        :param plugin_building_options:
        :type plugin_building_options: PluginBuildingOptions
        :param non_interactive:
        :type non_interactive: bool
        """
        if plugin_building_options.plugin_signing_password:
            _p = plugin_building_options.plugin_signing_password
        elif not non_interactive:
            _p = getpass('Plugin signing password: ')
        else:
            self._parser.error('no plugin signing password specified while in non-interactive mode')
        self._app.set_plugin_signing_password(lambda: _p)

    def _release_plugin(self,
                        command: TurtlesCommand.ReleasePluginCommand) -> None:
        """
        Implementation of the ``release-plugin`` command.

        :param command: The command object.
        :type command: TurtlesCommand.ReleasePluginCommand
        """
        errs = []
        for psc in command.get_plugin_set_catalogs():
            try:
                self._app.load_plugin_set_catalogs(psc)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        for ps in command.get_plugin_sets():
            try:
                self._app.load_plugin_sets(ps)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        for prc in command.get_plugin_registry_catalogs():
            try:
                self._app.load_plugin_registry_catalogs(prc)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        for pr in command.get_plugin_registries():
            try:
                self._app.load_plugin_registries(pr)
            except ValueError as ve:
                errs.append(ve)
            except ExceptionGroup as eg:
                errs.extend(eg.exceptions)
        try:
            self._app.load_plugin_signing_credentials(command.get_plugin_signing_credentials())
        except ValueError as ve:
            errs.append(ve)
        except ExceptionGroup as eg:
            errs.extend(eg.exceptions)
        if errs:
            raise ExceptionGroup(f'Errors while setting up the environment for deploying plugins', errs)
        self._obtain_plugin_signing_password(command, non_interactive=command.non_interactive)
        # Action
        # ... plugin_id -> list of (registry_id, layer_id, dst_path, plugin)
        ret = self._app.release_plugin(command.get_plugin_identifiers(),
                                       command.get_plugin_registry_layers(),
                                       interactive=not command.non_interactive)
        # Output
        print(tabulate.tabulate([[plugin_id, plugin.get_version(), registry_id, layer_id, dst_path] for plugin_id, val in ret.items() for registry_id, layer_id, dst_path, plugin in val],
                                headers=['Plugin identifier', 'Plugin version', 'Plugin registry', 'Plugin registry layer', 'Deployed JAR'],
                                tablefmt=command.output_format))

    def _rp(self, command: TurtlesCommand.ReleasePluginCommand) -> None:
        """
        Implementation of the ``rp`` command.

        :param command: The command object.
        :type command: TurtlesCommand.ReleasePluginCommand
        """
        self._release_plugin(command)

    def _version(self, command: StringCommand) -> None:
        """
        Implementation of the ``version`` command.

        :param command: The command object.
        :type command: StringCommand
        """
        self._do_string_command(command)


def main() -> None:
    """
    Main entry point of the module.
    """
    TurtlesCli().run()


# Main entry point of the module.
if __name__ == '__main__':
    main()
