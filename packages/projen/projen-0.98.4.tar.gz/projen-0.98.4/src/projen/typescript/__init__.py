from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from .._jsii import *

from .. import (
    GitOptions as _GitOptions_a65916a3,
    GroupRunnerOptions as _GroupRunnerOptions_148c59c1,
    IgnoreFileOptions as _IgnoreFileOptions_86c48b91,
    LoggerOptions as _LoggerOptions_eb0f6309,
    Project as _Project_57d89203,
    ProjectType as _ProjectType_fd80c725,
    ProjenrcFile as _ProjenrcFile_50432c7e,
    ProjenrcJsonOptions as _ProjenrcJsonOptions_9c40dd4f,
    ReleasableCommits as _ReleasableCommits_d481ce10,
    RenovatebotOptions as _RenovatebotOptions_18e6b8a1,
    SampleReadmeProps as _SampleReadmeProps_3518b03b,
    Task as _Task_9fa875b6,
)
from ..github import (
    AutoApproveOptions as _AutoApproveOptions_dac86cbe,
    AutoMergeOptions as _AutoMergeOptions_d112cd3c,
    DependabotOptions as _DependabotOptions_0cedc635,
    GitHubOptions as _GitHubOptions_21553699,
    GitIdentity as _GitIdentity_6effc3de,
    GithubCredentials as _GithubCredentials_ae257072,
    MergifyOptions as _MergifyOptions_a6faaab3,
    StaleOptions as _StaleOptions_929db764,
)
from ..github.workflows import (
    JobStep as _JobStep_c3287c05, Triggers as _Triggers_e9ae7617
)
from ..javascript import (
    BiomeOptions as _BiomeOptions_452ab984,
    BuildWorkflowOptions as _BuildWorkflowOptions_b756f97f,
    BundlerOptions as _BundlerOptions_d60b85ed,
    CodeArtifactOptions as _CodeArtifactOptions_e4782b3e,
    Eslint as _Eslint_b3991f7f,
    EslintOptions as _EslintOptions_824f60bb,
    JestOptions as _JestOptions_a085f64e,
    LicenseCheckerOptions as _LicenseCheckerOptions_80bcd362,
    NodePackageManager as _NodePackageManager_3eb53bf6,
    NodeProject as _NodeProject_b1a8841b,
    NodeProjectOptions as _NodeProjectOptions_d12f6f3b,
    NpmAccess as _NpmAccess_134fa228,
    PeerDependencyOptions as _PeerDependencyOptions_99d7d493,
    PrettierOptions as _PrettierOptions_41a5f203,
    ProjenrcOptions as _ProjenrcOptions_179dd39f,
    ScopedPackagesOptions as _ScopedPackagesOptions_52f0a477,
    TypeScriptCompilerOptions as _TypeScriptCompilerOptions_829fc4b0,
    TypeScriptImportsNotUsedAsValues as _TypeScriptImportsNotUsedAsValues_95cb8527,
    TypeScriptJsxMode as _TypeScriptJsxMode_8489d67f,
    TypeScriptModuleDetection as _TypeScriptModuleDetection_28bd432f,
    TypeScriptModuleResolution as _TypeScriptModuleResolution_56cffb1b,
    TypescriptConfig as _TypescriptConfig_e4a2920d,
    TypescriptConfigOptions as _TypescriptConfigOptions_8c5492cd,
    UpgradeDependenciesOptions as _UpgradeDependenciesOptions_1d8ce4da,
    YarnBerryOptions as _YarnBerryOptions_b6942539,
)
from ..release import (
    BranchOptions as _BranchOptions_13663d08,
    ReleaseTrigger as _ReleaseTrigger_e4dc221f,
)


class Projenrc(
    _ProjenrcFile_50432c7e,
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.Projenrc",
):
    '''(experimental) Sets up a typescript project to use TypeScript for projenrc.

    :stability: experimental
    '''

    def __init__(
        self,
        project: "TypeScriptProject",
        *,
        filename: typing.Optional[builtins.str] = None,
        projen_code_dir: typing.Optional[builtins.str] = None,
        swc: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param project: -
        :param filename: (experimental) The name of the projenrc file. Default: ".projenrc.ts"
        :param projen_code_dir: (experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file. Default: "projenrc"
        :param swc: (experimental) Whether to use ``SWC`` for ts-node. Default: false

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2263ee9c745ea47c774563d843521472e79762041f4e1ae7ba448b00eb619b8d)
            check_type(argname="argument project", value=project, expected_type=type_hints["project"])
        options = ProjenrcOptions(
            filename=filename, projen_code_dir=projen_code_dir, swc=swc
        )

        jsii.create(self.__class__, self, [project, options])

    @jsii.member(jsii_name="preSynthesize")
    def pre_synthesize(self) -> None:
        '''(experimental) Called before synthesis.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "preSynthesize", []))

    @builtins.property
    @jsii.member(jsii_name="filePath")
    def file_path(self) -> builtins.str:
        '''(experimental) The path of the projenrc file.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "filePath"))


@jsii.data_type(
    jsii_type="projen.typescript.ProjenrcOptions",
    jsii_struct_bases=[],
    name_mapping={
        "filename": "filename",
        "projen_code_dir": "projenCodeDir",
        "swc": "swc",
    },
)
class ProjenrcOptions:
    def __init__(
        self,
        *,
        filename: typing.Optional[builtins.str] = None,
        projen_code_dir: typing.Optional[builtins.str] = None,
        swc: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param filename: (experimental) The name of the projenrc file. Default: ".projenrc.ts"
        :param projen_code_dir: (experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file. Default: "projenrc"
        :param swc: (experimental) Whether to use ``SWC`` for ts-node. Default: false

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c19ece862a34d563e3af49bcb2633dab3ba4ac5f67cc57c6fff86d7cca41defc)
            check_type(argname="argument filename", value=filename, expected_type=type_hints["filename"])
            check_type(argname="argument projen_code_dir", value=projen_code_dir, expected_type=type_hints["projen_code_dir"])
            check_type(argname="argument swc", value=swc, expected_type=type_hints["swc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if filename is not None:
            self._values["filename"] = filename
        if projen_code_dir is not None:
            self._values["projen_code_dir"] = projen_code_dir
        if swc is not None:
            self._values["swc"] = swc

    @builtins.property
    def filename(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the projenrc file.

        :default: ".projenrc.ts"

        :stability: experimental
        '''
        result = self._values.get("filename")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projen_code_dir(self) -> typing.Optional[builtins.str]:
        '''(experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file.

        :default: "projenrc"

        :stability: experimental
        '''
        result = self._values.get("projen_code_dir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def swc(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Whether to use ``SWC`` for ts-node.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("swc")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ProjenrcOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ProjenrcTs(
    _ProjenrcFile_50432c7e,
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.ProjenrcTs",
):
    '''(experimental) A projenrc file written in TypeScript.

    This component can be instantiated in any type of project
    and has no expectations around the project's main language.

    Requires that ``npx`` is available.

    :stability: experimental
    '''

    def __init__(
        self,
        project: _Project_57d89203,
        *,
        filename: typing.Optional[builtins.str] = None,
        projen_code_dir: typing.Optional[builtins.str] = None,
        tsconfig_file_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param project: -
        :param filename: (experimental) The name of the projenrc file. Default: ".projenrc.ts"
        :param projen_code_dir: (experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file. Default: "projenrc"
        :param tsconfig_file_name: (experimental) The name of the tsconfig file that will be used by ts-node when compiling projen source files. Default: "tsconfig.projen.json"

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f8247bfab52de99210dd1174bf8292517bfb90aa0435a94a64a093bcdcceb1d3)
            check_type(argname="argument project", value=project, expected_type=type_hints["project"])
        options = ProjenrcTsOptions(
            filename=filename,
            projen_code_dir=projen_code_dir,
            tsconfig_file_name=tsconfig_file_name,
        )

        jsii.create(self.__class__, self, [project, options])

    @jsii.member(jsii_name="preSynthesize")
    def pre_synthesize(self) -> None:
        '''(experimental) Called before synthesis.

        :stability: experimental
        '''
        return typing.cast(None, jsii.invoke(self, "preSynthesize", []))

    @builtins.property
    @jsii.member(jsii_name="filePath")
    def file_path(self) -> builtins.str:
        '''(experimental) The path of the projenrc file.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "filePath"))

    @builtins.property
    @jsii.member(jsii_name="tsconfig")
    def tsconfig(self) -> _TypescriptConfig_e4a2920d:
        '''(experimental) TypeScript configuration file used to compile projen source files.

        :stability: experimental
        '''
        return typing.cast(_TypescriptConfig_e4a2920d, jsii.get(self, "tsconfig"))


@jsii.data_type(
    jsii_type="projen.typescript.ProjenrcTsOptions",
    jsii_struct_bases=[],
    name_mapping={
        "filename": "filename",
        "projen_code_dir": "projenCodeDir",
        "tsconfig_file_name": "tsconfigFileName",
    },
)
class ProjenrcTsOptions:
    def __init__(
        self,
        *,
        filename: typing.Optional[builtins.str] = None,
        projen_code_dir: typing.Optional[builtins.str] = None,
        tsconfig_file_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param filename: (experimental) The name of the projenrc file. Default: ".projenrc.ts"
        :param projen_code_dir: (experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file. Default: "projenrc"
        :param tsconfig_file_name: (experimental) The name of the tsconfig file that will be used by ts-node when compiling projen source files. Default: "tsconfig.projen.json"

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__160fd3491644df95d187ac5907c3e3cc1eb206baf5e8a1cbfca8496701ab6df6)
            check_type(argname="argument filename", value=filename, expected_type=type_hints["filename"])
            check_type(argname="argument projen_code_dir", value=projen_code_dir, expected_type=type_hints["projen_code_dir"])
            check_type(argname="argument tsconfig_file_name", value=tsconfig_file_name, expected_type=type_hints["tsconfig_file_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if filename is not None:
            self._values["filename"] = filename
        if projen_code_dir is not None:
            self._values["projen_code_dir"] = projen_code_dir
        if tsconfig_file_name is not None:
            self._values["tsconfig_file_name"] = tsconfig_file_name

    @builtins.property
    def filename(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the projenrc file.

        :default: ".projenrc.ts"

        :stability: experimental
        '''
        result = self._values.get("filename")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projen_code_dir(self) -> typing.Optional[builtins.str]:
        '''(experimental) A directory tree that may contain *.ts files that can be referenced from your projenrc typescript file.

        :default: "projenrc"

        :stability: experimental
        '''
        result = self._values.get("projen_code_dir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tsconfig_file_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the tsconfig file that will be used by ts-node when compiling projen source files.

        :default: "tsconfig.projen.json"

        :stability: experimental
        '''
        result = self._values.get("tsconfig_file_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ProjenrcTsOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TsJestBabelConfig(
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TsJestBabelConfig",
):
    '''
    :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options/babelConfig/
    :stability: experimental
    '''

    @jsii.member(jsii_name="autoDetectConfig")
    @builtins.classmethod
    def auto_detect_config(cls) -> "TsJestBabelConfig":
        '''(experimental) Enables Babel processing.

        ``ts-jest`` will try to find an existing Babel configuration and pass it to the ``babel-jest`` processor.

        :stability: experimental
        '''
        return typing.cast("TsJestBabelConfig", jsii.sinvoke(cls, "autoDetectConfig", []))

    @jsii.member(jsii_name="custom")
    @builtins.classmethod
    def custom(
        cls,
        config: typing.Mapping[builtins.str, typing.Any],
    ) -> "TsJestBabelConfig":
        '''(experimental) Inline compiler options.

        :param config: -

        :see: https://babeljs.io/docs/options
        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57c74312f3b84d4697a7e445fdef068f4807b51470030ba0ac243d70498c8bca)
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        return typing.cast("TsJestBabelConfig", jsii.sinvoke(cls, "custom", [config]))

    @jsii.member(jsii_name="disabled")
    @builtins.classmethod
    def disabled(cls) -> "TsJestBabelConfig":
        '''(experimental) Disables the use of Babel.

        :stability: experimental
        '''
        return typing.cast("TsJestBabelConfig", jsii.sinvoke(cls, "disabled", []))

    @jsii.member(jsii_name="fromFile")
    @builtins.classmethod
    def from_file(cls, file_path: builtins.str) -> "TsJestBabelConfig":
        '''(experimental) Path to a babelrc file.

        The path should be relative to the current working directory where you start Jest from. You can also use ``<rootDir>`` in the path.

        :param file_path: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa38b428b489eb4f2e5ab1fa56039a74d05152687403b422fe16578573506d72)
            check_type(argname="argument file_path", value=file_path, expected_type=type_hints["file_path"])
        return typing.cast("TsJestBabelConfig", jsii.sinvoke(cls, "fromFile", [file_path]))


class TsJestDiagnostics(
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TsJestDiagnostics",
):
    '''
    :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options/diagnostics/
    :stability: experimental
    '''

    @jsii.member(jsii_name="all")
    @builtins.classmethod
    def all(cls) -> "TsJestDiagnostics":
        '''(experimental) Enable all diagnostics.

        :stability: experimental
        '''
        return typing.cast("TsJestDiagnostics", jsii.sinvoke(cls, "all", []))

    @jsii.member(jsii_name="custom")
    @builtins.classmethod
    def custom(
        cls,
        config: typing.Mapping[builtins.str, typing.Any],
    ) -> "TsJestDiagnostics":
        '''(experimental) Provide a custom diagnostics configuration.

        :param config: -

        :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options/diagnostics/
        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__abb08ee9151f9ffaafab18cc1dd48f6143d5328362bb1f2c80aa95d395bbde58)
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        return typing.cast("TsJestDiagnostics", jsii.sinvoke(cls, "custom", [config]))

    @jsii.member(jsii_name="none")
    @builtins.classmethod
    def none(cls) -> "TsJestDiagnostics":
        '''(experimental) Disable all diagnostics.

        :stability: experimental
        '''
        return typing.cast("TsJestDiagnostics", jsii.sinvoke(cls, "none", []))


@jsii.data_type(
    jsii_type="projen.typescript.TsJestOptions",
    jsii_struct_bases=[],
    name_mapping={
        "transform_options": "transformOptions",
        "transform_pattern": "transformPattern",
    },
)
class TsJestOptions:
    def __init__(
        self,
        *,
        transform_options: typing.Optional[typing.Union["TsJestTransformOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        transform_pattern: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param transform_options: (experimental) Override the default ts-jest transformer configuration.
        :param transform_pattern: (experimental) Which files should ts-jest act upon. Default: "^.+\\.[t]sx?$"

        :stability: experimental
        '''
        if isinstance(transform_options, dict):
            transform_options = TsJestTransformOptions(**transform_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8c225926587b822ce73ff151cc8d04de0c607d2d0315e5c10b19bf90177fe777)
            check_type(argname="argument transform_options", value=transform_options, expected_type=type_hints["transform_options"])
            check_type(argname="argument transform_pattern", value=transform_pattern, expected_type=type_hints["transform_pattern"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if transform_options is not None:
            self._values["transform_options"] = transform_options
        if transform_pattern is not None:
            self._values["transform_pattern"] = transform_pattern

    @builtins.property
    def transform_options(self) -> typing.Optional["TsJestTransformOptions"]:
        '''(experimental) Override the default ts-jest transformer configuration.

        :stability: experimental
        '''
        result = self._values.get("transform_options")
        return typing.cast(typing.Optional["TsJestTransformOptions"], result)

    @builtins.property
    def transform_pattern(self) -> typing.Optional[builtins.str]:
        '''(experimental) Which files should ts-jest act upon.

        :default: "^.+\\.[t]sx?$"

        :see: https://jestjs.io/docs/configuration#transform-objectstring-pathtotransformer--pathtotransformer-object
        :stability: experimental
        '''
        result = self._values.get("transform_pattern")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TsJestOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="projen.typescript.TsJestTransformOptions",
    jsii_struct_bases=[],
    name_mapping={
        "ast_transformers": "astTransformers",
        "babel_config": "babelConfig",
        "compiler": "compiler",
        "diagnostics": "diagnostics",
        "isolated_modules": "isolatedModules",
        "stringify_content_path_regex": "stringifyContentPathRegex",
        "tsconfig": "tsconfig",
        "use_esm": "useESM",
    },
)
class TsJestTransformOptions:
    def __init__(
        self,
        *,
        ast_transformers: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        babel_config: typing.Optional[TsJestBabelConfig] = None,
        compiler: typing.Optional[builtins.str] = None,
        diagnostics: typing.Optional[TsJestDiagnostics] = None,
        isolated_modules: typing.Optional[builtins.bool] = None,
        stringify_content_path_regex: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional["TsJestTsconfig"] = None,
        use_esm: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param ast_transformers: (experimental) Custom TypeScript AST transformers. Default: auto
        :param babel_config: (experimental) Babel(Jest) related configuration. Default: TsJestBabelConfig.disabled()
        :param compiler: (experimental) TypeScript module to use as compiler. Default: "typescript"
        :param diagnostics: (experimental) Diagnostics related configuration. Default: TsJestDiagnostics.all()
        :param isolated_modules: (experimental) Run ts-jest tests with this TSConfig isolatedModules setting. You'll lose type-checking ability and some features such as const enum, but in the case you plan on using Jest with the cache disabled (jest --no-cache), your tests will then run much faster. Default: false
        :param stringify_content_path_regex: (experimental) Files which will become modules returning self content. Default: disabled
        :param tsconfig: (experimental) TypeScript compiler related configuration. Default: - Your project's ``tsconfigDev`` file.
        :param use_esm: (experimental) Enable ESM support. Default: auto

        :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options
        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1dea54f53ed685b6629951d7aaee8ae0563b656a849a1c5f2cf70786f2333cb1)
            check_type(argname="argument ast_transformers", value=ast_transformers, expected_type=type_hints["ast_transformers"])
            check_type(argname="argument babel_config", value=babel_config, expected_type=type_hints["babel_config"])
            check_type(argname="argument compiler", value=compiler, expected_type=type_hints["compiler"])
            check_type(argname="argument diagnostics", value=diagnostics, expected_type=type_hints["diagnostics"])
            check_type(argname="argument isolated_modules", value=isolated_modules, expected_type=type_hints["isolated_modules"])
            check_type(argname="argument stringify_content_path_regex", value=stringify_content_path_regex, expected_type=type_hints["stringify_content_path_regex"])
            check_type(argname="argument tsconfig", value=tsconfig, expected_type=type_hints["tsconfig"])
            check_type(argname="argument use_esm", value=use_esm, expected_type=type_hints["use_esm"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ast_transformers is not None:
            self._values["ast_transformers"] = ast_transformers
        if babel_config is not None:
            self._values["babel_config"] = babel_config
        if compiler is not None:
            self._values["compiler"] = compiler
        if diagnostics is not None:
            self._values["diagnostics"] = diagnostics
        if isolated_modules is not None:
            self._values["isolated_modules"] = isolated_modules
        if stringify_content_path_regex is not None:
            self._values["stringify_content_path_regex"] = stringify_content_path_regex
        if tsconfig is not None:
            self._values["tsconfig"] = tsconfig
        if use_esm is not None:
            self._values["use_esm"] = use_esm

    @builtins.property
    def ast_transformers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''(experimental) Custom TypeScript AST transformers.

        :default: auto

        :stability: experimental
        '''
        result = self._values.get("ast_transformers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def babel_config(self) -> typing.Optional[TsJestBabelConfig]:
        '''(experimental) Babel(Jest) related configuration.

        :default: TsJestBabelConfig.disabled()

        :stability: experimental
        '''
        result = self._values.get("babel_config")
        return typing.cast(typing.Optional[TsJestBabelConfig], result)

    @builtins.property
    def compiler(self) -> typing.Optional[builtins.str]:
        '''(experimental) TypeScript module to use as compiler.

        :default: "typescript"

        :stability: experimental
        '''
        result = self._values.get("compiler")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def diagnostics(self) -> typing.Optional[TsJestDiagnostics]:
        '''(experimental) Diagnostics related configuration.

        :default: TsJestDiagnostics.all()

        :stability: experimental
        '''
        result = self._values.get("diagnostics")
        return typing.cast(typing.Optional[TsJestDiagnostics], result)

    @builtins.property
    def isolated_modules(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Run ts-jest tests with this TSConfig isolatedModules setting.

        You'll lose type-checking ability and some features such as const enum, but in the case you plan on using Jest with the cache disabled (jest --no-cache), your tests will then run much faster.

        :default: false

        :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options/isolatedModules
        :stability: experimental
        '''
        result = self._values.get("isolated_modules")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def stringify_content_path_regex(self) -> typing.Optional[builtins.str]:
        '''(experimental) Files which will become modules returning self content.

        :default: disabled

        :stability: experimental
        '''
        result = self._values.get("stringify_content_path_regex")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tsconfig(self) -> typing.Optional["TsJestTsconfig"]:
        '''(experimental) TypeScript compiler related configuration.

        :default: - Your project's ``tsconfigDev`` file.

        :stability: experimental
        '''
        result = self._values.get("tsconfig")
        return typing.cast(typing.Optional["TsJestTsconfig"], result)

    @builtins.property
    def use_esm(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable ESM support.

        :default: auto

        :stability: experimental
        '''
        result = self._values.get("use_esm")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TsJestTransformOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TsJestTsconfig(
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TsJestTsconfig",
):
    '''
    :see: https://kulshekhar.github.io/ts-jest/docs/getting-started/options/tsconfig/
    :stability: experimental
    '''

    @jsii.member(jsii_name="auto")
    @builtins.classmethod
    def auto(cls) -> "TsJestTsconfig":
        '''(experimental) Uses ``tsconfig.json`` if found, or the built-in default TypeScript compiler options.

        :stability: experimental
        '''
        return typing.cast("TsJestTsconfig", jsii.sinvoke(cls, "auto", []))

    @jsii.member(jsii_name="builtInDefaults")
    @builtins.classmethod
    def built_in_defaults(cls) -> "TsJestTsconfig":
        '''(experimental) Force`` ts-jest`` to use its built-in defaults even if there is a ``tsconfig.json`` in your project.

        :stability: experimental
        '''
        return typing.cast("TsJestTsconfig", jsii.sinvoke(cls, "builtInDefaults", []))

    @jsii.member(jsii_name="custom")
    @builtins.classmethod
    def custom(
        cls,
        *,
        allow_arbitrary_extensions: typing.Optional[builtins.bool] = None,
        allow_importing_ts_extensions: typing.Optional[builtins.bool] = None,
        allow_js: typing.Optional[builtins.bool] = None,
        allow_synthetic_default_imports: typing.Optional[builtins.bool] = None,
        allow_unreachable_code: typing.Optional[builtins.bool] = None,
        allow_unused_labels: typing.Optional[builtins.bool] = None,
        always_strict: typing.Optional[builtins.bool] = None,
        base_url: typing.Optional[builtins.str] = None,
        check_js: typing.Optional[builtins.bool] = None,
        custom_conditions: typing.Optional[typing.Sequence[builtins.str]] = None,
        declaration: typing.Optional[builtins.bool] = None,
        declaration_dir: typing.Optional[builtins.str] = None,
        declaration_map: typing.Optional[builtins.bool] = None,
        downlevel_iteration: typing.Optional[builtins.bool] = None,
        emit_declaration_only: typing.Optional[builtins.bool] = None,
        emit_decorator_metadata: typing.Optional[builtins.bool] = None,
        es_module_interop: typing.Optional[builtins.bool] = None,
        exact_optional_property_types: typing.Optional[builtins.bool] = None,
        experimental_decorators: typing.Optional[builtins.bool] = None,
        force_consistent_casing_in_file_names: typing.Optional[builtins.bool] = None,
        imports_not_used_as_values: typing.Optional[_TypeScriptImportsNotUsedAsValues_95cb8527] = None,
        incremental: typing.Optional[builtins.bool] = None,
        inline_source_map: typing.Optional[builtins.bool] = None,
        inline_sources: typing.Optional[builtins.bool] = None,
        isolated_modules: typing.Optional[builtins.bool] = None,
        jsx: typing.Optional[_TypeScriptJsxMode_8489d67f] = None,
        jsx_import_source: typing.Optional[builtins.str] = None,
        lib: typing.Optional[typing.Sequence[builtins.str]] = None,
        module: typing.Optional[builtins.str] = None,
        module_detection: typing.Optional[_TypeScriptModuleDetection_28bd432f] = None,
        module_resolution: typing.Optional[_TypeScriptModuleResolution_56cffb1b] = None,
        no_emit: typing.Optional[builtins.bool] = None,
        no_emit_on_error: typing.Optional[builtins.bool] = None,
        no_fallthrough_cases_in_switch: typing.Optional[builtins.bool] = None,
        no_implicit_any: typing.Optional[builtins.bool] = None,
        no_implicit_override: typing.Optional[builtins.bool] = None,
        no_implicit_returns: typing.Optional[builtins.bool] = None,
        no_implicit_this: typing.Optional[builtins.bool] = None,
        no_property_access_from_index_signature: typing.Optional[builtins.bool] = None,
        no_unchecked_indexed_access: typing.Optional[builtins.bool] = None,
        no_unused_locals: typing.Optional[builtins.bool] = None,
        no_unused_parameters: typing.Optional[builtins.bool] = None,
        out_dir: typing.Optional[builtins.str] = None,
        paths: typing.Optional[typing.Mapping[builtins.str, typing.Sequence[builtins.str]]] = None,
        resolve_json_module: typing.Optional[builtins.bool] = None,
        resolve_package_json_exports: typing.Optional[builtins.bool] = None,
        resolve_package_json_imports: typing.Optional[builtins.bool] = None,
        root_dir: typing.Optional[builtins.str] = None,
        skip_lib_check: typing.Optional[builtins.bool] = None,
        source_map: typing.Optional[builtins.bool] = None,
        source_root: typing.Optional[builtins.str] = None,
        strict: typing.Optional[builtins.bool] = None,
        strict_null_checks: typing.Optional[builtins.bool] = None,
        strict_property_initialization: typing.Optional[builtins.bool] = None,
        strip_internal: typing.Optional[builtins.bool] = None,
        target: typing.Optional[builtins.str] = None,
        ts_build_info_file: typing.Optional[builtins.str] = None,
        type_roots: typing.Optional[typing.Sequence[builtins.str]] = None,
        types: typing.Optional[typing.Sequence[builtins.str]] = None,
        use_unknown_in_catch_variables: typing.Optional[builtins.bool] = None,
        verbatim_module_syntax: typing.Optional[builtins.bool] = None,
    ) -> "TsJestTsconfig":
        '''(experimental) Inline compiler options.

        :param allow_arbitrary_extensions: (experimental) Suppress arbitrary extension import errors with the assumption that a bundler will be handling it. Default: undefined
        :param allow_importing_ts_extensions: (experimental) Allows TypeScript files to import each other with TypeScript-specific extensions (``.ts``, ``.mts``, ``.tsx``). Requires ``noEmit`` or ``emitDeclarationOnly``. Default: undefined
        :param allow_js: (experimental) Allow JavaScript files to be compiled. Default: false
        :param allow_synthetic_default_imports: (experimental) Allow default imports from modules with no default export. This does not affect code emit, just typechecking.
        :param allow_unreachable_code: (experimental) Allow Unreachable Code. When: - ``undefined`` (default) provide suggestions as warnings to editors - ``true`` unreachable code is ignored - ``false`` raises compiler errors about unreachable code These warnings are only about code which is provably unreachable due to the use of JavaScript syntax.
        :param allow_unused_labels: (experimental) Allow Unused Labels. When: - ``undefined`` (default) provide suggestions as warnings to editors - ``true`` unused labels are ignored - ``false`` raises compiler errors about unused labels Labels are very rare in JavaScript and typically indicate an attempt to write an object literal:: function verifyAge(age: number) { // Forgot 'return' statement if (age > 18) { verified: true; // ^^^^^^^^ Unused label. } }
        :param always_strict: (experimental) Ensures that your files are parsed in the ECMAScript strict mode, and emit “use strict” for each source file. Default: true
        :param base_url: (experimental) Lets you set a base directory to resolve non-absolute module names. You can define a root folder where you can do absolute file resolution.
        :param check_js: (experimental) Check JS. Works in tandem with `allowJs <https://www.typescriptlang.org/tsconfig#allowJs>`_. When checkJs is enabled then errors are reported in JavaScript files. This is the equivalent of including //
        :param custom_conditions: (experimental) List of additional conditions that should succeed when TypeScript resolves from an ``exports`` or ``imports`` field of a ``package.json``. Default: undefined
        :param declaration: (experimental) To be specified along with the above.
        :param declaration_dir: (experimental) Offers a way to configure the root directory for where declaration files are emitted.
        :param declaration_map: (experimental) Generates a source map for .d.ts files which map back to the original .ts source file. This will allow editors such as VS Code to go to the original .ts file when using features like Go to Definition.
        :param downlevel_iteration: (experimental) Downleveling is TypeScript’s term for transpiling to an older version of JavaScript. This flag is to enable support for a more accurate implementation of how modern JavaScript iterates through new concepts in older JavaScript runtimes. ECMAScript 6 added several new iteration primitives: the for / of loop (for (el of arr)), Array spread ([a, ...b]), argument spread (fn(...args)), and Symbol.iterator. downlevelIteration allows for these iteration primitives to be used more accurately in ES5 environments if a Symbol.iterator implementation is present.
        :param emit_declaration_only: (experimental) Only emit .d.ts files; do not emit .js files. Default: false
        :param emit_decorator_metadata: (experimental) Enables experimental support for decorators, which is in stage 2 of the TC39 standardization process. Decorators are a language feature which hasn’t yet been fully ratified into the JavaScript specification. This means that the implementation version in TypeScript may differ from the implementation in JavaScript when it it decided by TC39. You can find out more about decorator support in TypeScript in the handbook. Default: undefined
        :param es_module_interop: (experimental) Emit __importStar and __importDefault helpers for runtime babel ecosystem compatibility and enable --allowSyntheticDefaultImports for typesystem compatibility. Default: false
        :param exact_optional_property_types: (experimental) Specifies that optional property types should be interpreted exactly as written, meaning that ``| undefined`` is not added to the type Available with TypeScript 4.4 and newer. Default: false
        :param experimental_decorators: (experimental) Enables experimental support for decorators, which is in stage 2 of the TC39 standardization process. Default: true
        :param force_consistent_casing_in_file_names: (experimental) Disallow inconsistently-cased references to the same file. Default: false
        :param imports_not_used_as_values: (experimental) This flag works because you can use ``import type`` to explicitly create an ``import`` statement which should never be emitted into JavaScript. Default: "remove"
        :param incremental: (experimental) Tells TypeScript to save information about the project graph from the last compilation to files stored on disk. This creates a series of .tsbuildinfo files in the same folder as your compilation output. They are not used by your JavaScript at runtime and can be safely deleted. You can read more about the flag in the 3.4 release notes.
        :param inline_source_map: (experimental) When set, instead of writing out a .js.map file to provide source maps, TypeScript will embed the source map content in the .js files. Default: true
        :param inline_sources: (experimental) When set, TypeScript will include the original content of the .ts file as an embedded string in the source map. This is often useful in the same cases as inlineSourceMap. Default: true
        :param isolated_modules: (experimental) Perform additional checks to ensure that separate compilation (such as with transpileModule or. Default: false
        :param jsx: (experimental) Support JSX in .tsx files: "react", "preserve", "react-native" etc. Default: undefined
        :param jsx_import_source: (experimental) Declares the module specifier to be used for importing the jsx and jsxs factory functions when using jsx. Default: undefined
        :param lib: (experimental) Reference for type definitions / libraries to use (eg. ES2016, ES5, ES2018). Default: [ "es2018" ]
        :param module: (experimental) Sets the module system for the program. See https://www.typescriptlang.org/docs/handbook/modules.html#ambient-modules. Default: "CommonJS"
        :param module_detection: (experimental) This setting controls how TypeScript determines whether a file is a `script or a module <https://www.typescriptlang.org/docs/handbook/modules/theory.html#scripts-and-modules-in-javascript>`_. Default: "auto"
        :param module_resolution: (experimental) Determine how modules get resolved. Either "Node" for Node.js/io.js style resolution, or "Classic". Default: "node"
        :param no_emit: (experimental) Do not emit outputs. Default: false
        :param no_emit_on_error: (experimental) Do not emit compiler output files like JavaScript source code, source-maps or declarations if any errors were reported. Default: true
        :param no_fallthrough_cases_in_switch: (experimental) Report errors for fallthrough cases in switch statements. Ensures that any non-empty case inside a switch statement includes either break or return. This means you won’t accidentally ship a case fallthrough bug. Default: true
        :param no_implicit_any: (experimental) In some cases where no type annotations are present, TypeScript will fall back to a type of any for a variable when it cannot infer the type. Default: true
        :param no_implicit_override: (experimental) Using ``noImplicitOverride``, you can ensure that sub-classes never go out of sync as they are required to explicitly declare that they are overriding a member using the ``override`` keyword. This also improves readability of the programmer's intent. Available with TypeScript 4.3 and newer. Default: false
        :param no_implicit_returns: (experimental) When enabled, TypeScript will check all code paths in a function to ensure they return a value. Default: true
        :param no_implicit_this: (experimental) Raise error on ‘this’ expressions with an implied ‘any’ type. Default: true
        :param no_property_access_from_index_signature: (experimental) Raise error on use of the dot syntax to access fields which are not defined. Default: true
        :param no_unchecked_indexed_access: (experimental) Raise error when accessing indexes on objects with unknown keys defined in index signatures. Default: true
        :param no_unused_locals: (experimental) Report errors on unused local variables. Default: true
        :param no_unused_parameters: (experimental) Report errors on unused parameters in functions. Default: true
        :param out_dir: (experimental) Output directory for the compiled files.
        :param paths: (experimental) A series of entries which re-map imports to lookup locations relative to the baseUrl, there is a larger coverage of paths in the handbook. paths lets you declare how TypeScript should resolve an import in your require/imports.
        :param resolve_json_module: (experimental) Allows importing modules with a ‘.json’ extension, which is a common practice in node projects. This includes generating a type for the import based on the static JSON shape. Default: true
        :param resolve_package_json_exports: (experimental) Forces TypeScript to consult the ``exports`` field of ``package.json`` files if it ever reads from a package in ``node_modules``. Default: true
        :param resolve_package_json_imports: (experimental) Forces TypeScript to consult the ``imports`` field of ``package.json`` when performing a lookup that begins with ``#`` from a file that has a ``package.json`` as an ancestor. Default: undefined
        :param root_dir: (experimental) Specifies the root directory of input files. Only use to control the output directory structure with ``outDir``.
        :param skip_lib_check: (experimental) Skip type checking of all declaration files (*.d.ts). Default: false
        :param source_map: (experimental) Enables the generation of sourcemap files. Default: undefined
        :param source_root: (experimental) Specify the location where a debugger should locate TypeScript files instead of relative source locations. Default: undefined
        :param strict: (experimental) The strict flag enables a wide range of type checking behavior that results in stronger guarantees of program correctness. Turning this on is equivalent to enabling all of the strict mode family options, which are outlined below. You can then turn off individual strict mode family checks as needed. Default: true
        :param strict_null_checks: (experimental) When strictNullChecks is false, null and undefined are effectively ignored by the language. This can lead to unexpected errors at runtime. When strictNullChecks is true, null and undefined have their own distinct types and you’ll get a type error if you try to use them where a concrete value is expected. Default: true
        :param strict_property_initialization: (experimental) When set to true, TypeScript will raise an error when a class property was declared but not set in the constructor. Default: true
        :param strip_internal: (experimental) Do not emit declarations for code that has an ``@internal`` annotation in it’s JSDoc comment. Default: true
        :param target: (experimental) Modern browsers support all ES6 features, so ES6 is a good choice. You might choose to set a lower target if your code is deployed to older environments, or a higher target if your code is guaranteed to run in newer environments. Default: "ES2018"
        :param ts_build_info_file: (experimental) This setting lets you specify a file for storing incremental compilation information as a part of composite projects which enables faster building of larger TypeScript codebases. You can read more about composite projects in the handbook.
        :param type_roots: (experimental) If typeRoots is specified, only packages under typeRoots will be included.
        :param types: (experimental) If types is specified, only packages listed will be included in the global scope.
        :param use_unknown_in_catch_variables: (experimental) Change the type of the variable in a catch clause from any to unknown Available with TypeScript 4.4 and newer. Default: true
        :param verbatim_module_syntax: (experimental) Simplifies TypeScript's handling of import/export ``type`` modifiers. Default: undefined

        :see: TypeScriptCompilerOptions
        :stability: experimental
        '''
        config = _TypeScriptCompilerOptions_829fc4b0(
            allow_arbitrary_extensions=allow_arbitrary_extensions,
            allow_importing_ts_extensions=allow_importing_ts_extensions,
            allow_js=allow_js,
            allow_synthetic_default_imports=allow_synthetic_default_imports,
            allow_unreachable_code=allow_unreachable_code,
            allow_unused_labels=allow_unused_labels,
            always_strict=always_strict,
            base_url=base_url,
            check_js=check_js,
            custom_conditions=custom_conditions,
            declaration=declaration,
            declaration_dir=declaration_dir,
            declaration_map=declaration_map,
            downlevel_iteration=downlevel_iteration,
            emit_declaration_only=emit_declaration_only,
            emit_decorator_metadata=emit_decorator_metadata,
            es_module_interop=es_module_interop,
            exact_optional_property_types=exact_optional_property_types,
            experimental_decorators=experimental_decorators,
            force_consistent_casing_in_file_names=force_consistent_casing_in_file_names,
            imports_not_used_as_values=imports_not_used_as_values,
            incremental=incremental,
            inline_source_map=inline_source_map,
            inline_sources=inline_sources,
            isolated_modules=isolated_modules,
            jsx=jsx,
            jsx_import_source=jsx_import_source,
            lib=lib,
            module=module,
            module_detection=module_detection,
            module_resolution=module_resolution,
            no_emit=no_emit,
            no_emit_on_error=no_emit_on_error,
            no_fallthrough_cases_in_switch=no_fallthrough_cases_in_switch,
            no_implicit_any=no_implicit_any,
            no_implicit_override=no_implicit_override,
            no_implicit_returns=no_implicit_returns,
            no_implicit_this=no_implicit_this,
            no_property_access_from_index_signature=no_property_access_from_index_signature,
            no_unchecked_indexed_access=no_unchecked_indexed_access,
            no_unused_locals=no_unused_locals,
            no_unused_parameters=no_unused_parameters,
            out_dir=out_dir,
            paths=paths,
            resolve_json_module=resolve_json_module,
            resolve_package_json_exports=resolve_package_json_exports,
            resolve_package_json_imports=resolve_package_json_imports,
            root_dir=root_dir,
            skip_lib_check=skip_lib_check,
            source_map=source_map,
            source_root=source_root,
            strict=strict,
            strict_null_checks=strict_null_checks,
            strict_property_initialization=strict_property_initialization,
            strip_internal=strip_internal,
            target=target,
            ts_build_info_file=ts_build_info_file,
            type_roots=type_roots,
            types=types,
            use_unknown_in_catch_variables=use_unknown_in_catch_variables,
            verbatim_module_syntax=verbatim_module_syntax,
        )

        return typing.cast("TsJestTsconfig", jsii.sinvoke(cls, "custom", [config]))

    @jsii.member(jsii_name="fromFile")
    @builtins.classmethod
    def from_file(cls, file_path: builtins.str) -> "TsJestTsconfig":
        '''(experimental) Path to a ``tsconfig`` file.

        The path should be relative to the current working directory where you start Jest from. You can also use ``<rootDir>`` in the path to start from the project root dir.

        :param file_path: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__92dd15c4a7cabe98b93189ec1f931bb163c5658476fc9627211024b208dcbf8f)
            check_type(argname="argument file_path", value=file_path, expected_type=type_hints["file_path"])
        return typing.cast("TsJestTsconfig", jsii.sinvoke(cls, "fromFile", [file_path]))


class TypeScriptProject(
    _NodeProject_b1a8841b,
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TypeScriptProject",
):
    '''(experimental) TypeScript project.

    :stability: experimental
    :pjid: typescript
    '''

    def __init__(
        self,
        *,
        disable_tsconfig: typing.Optional[builtins.bool] = None,
        disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
        docgen: typing.Optional[builtins.bool] = None,
        docs_directory: typing.Optional[builtins.str] = None,
        entrypoint_types: typing.Optional[builtins.str] = None,
        eslint: typing.Optional[builtins.bool] = None,
        eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
        libdir: typing.Optional[builtins.str] = None,
        projenrc_ts: typing.Optional[builtins.bool] = None,
        projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        sample_code: typing.Optional[builtins.bool] = None,
        srcdir: typing.Optional[builtins.str] = None,
        testdir: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev_file: typing.Optional[builtins.str] = None,
        ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        typescript_version: typing.Optional[builtins.str] = None,
        default_release_branch: builtins.str,
        artifacts_directory: typing.Optional[builtins.str] = None,
        auto_approve_upgrades: typing.Optional[builtins.bool] = None,
        biome: typing.Optional[builtins.bool] = None,
        biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow: typing.Optional[builtins.bool] = None,
        build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
        bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
        check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
        code_cov: typing.Optional[builtins.bool] = None,
        code_cov_token_secret: typing.Optional[builtins.str] = None,
        copyright_owner: typing.Optional[builtins.str] = None,
        copyright_period: typing.Optional[builtins.str] = None,
        dependabot: typing.Optional[builtins.bool] = None,
        dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
        deps_upgrade: typing.Optional[builtins.bool] = None,
        deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
        gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        jest: typing.Optional[builtins.bool] = None,
        jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
        mutable_build: typing.Optional[builtins.bool] = None,
        npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        npmignore_enabled: typing.Optional[builtins.bool] = None,
        npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        package: typing.Optional[builtins.bool] = None,
        prettier: typing.Optional[builtins.bool] = None,
        prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_dev_dependency: typing.Optional[builtins.bool] = None,
        projenrc_js: typing.Optional[builtins.bool] = None,
        projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_version: typing.Optional[builtins.str] = None,
        pull_request_template: typing.Optional[builtins.bool] = None,
        pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
        release: typing.Optional[builtins.bool] = None,
        release_to_npm: typing.Optional[builtins.bool] = None,
        release_workflow: typing.Optional[builtins.bool] = None,
        workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
        workflow_node_version: typing.Optional[builtins.str] = None,
        workflow_package_cache: typing.Optional[builtins.bool] = None,
        auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_merge: typing.Optional[builtins.bool] = None,
        auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
        clobber: typing.Optional[builtins.bool] = None,
        dev_container: typing.Optional[builtins.bool] = None,
        github: typing.Optional[builtins.bool] = None,
        github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
        gitpod: typing.Optional[builtins.bool] = None,
        mergify: typing.Optional[builtins.bool] = None,
        mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
        project_type: typing.Optional[_ProjectType_fd80c725] = None,
        projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
        projen_token_secret: typing.Optional[builtins.str] = None,
        readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
        stale: typing.Optional[builtins.bool] = None,
        stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
        vscode: typing.Optional[builtins.bool] = None,
        allow_library_dependencies: typing.Optional[builtins.bool] = None,
        author_email: typing.Optional[builtins.str] = None,
        author_name: typing.Optional[builtins.str] = None,
        author_organization: typing.Optional[builtins.bool] = None,
        author_url: typing.Optional[builtins.str] = None,
        auto_detect_bin: typing.Optional[builtins.bool] = None,
        bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        bugs_email: typing.Optional[builtins.str] = None,
        bugs_url: typing.Optional[builtins.str] = None,
        bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        bun_version: typing.Optional[builtins.str] = None,
        code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
        deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[builtins.str] = None,
        homepage: typing.Optional[builtins.str] = None,
        keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
        license: typing.Optional[builtins.str] = None,
        licensed: typing.Optional[builtins.bool] = None,
        max_node_version: typing.Optional[builtins.str] = None,
        min_node_version: typing.Optional[builtins.str] = None,
        npm_access: typing.Optional[_NpmAccess_134fa228] = None,
        npm_provenance: typing.Optional[builtins.bool] = None,
        npm_registry: typing.Optional[builtins.str] = None,
        npm_registry_url: typing.Optional[builtins.str] = None,
        npm_token_secret: typing.Optional[builtins.str] = None,
        npm_trusted_publishing: typing.Optional[builtins.bool] = None,
        package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
        package_name: typing.Optional[builtins.str] = None,
        peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
        peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        pnpm_version: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        repository_directory: typing.Optional[builtins.str] = None,
        scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
        scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        stability: typing.Optional[builtins.str] = None,
        yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
        bump_package: typing.Optional[builtins.str] = None,
        jsii_release_version: typing.Optional[builtins.str] = None,
        major_version: typing.Optional[jsii.Number] = None,
        min_major_version: typing.Optional[jsii.Number] = None,
        next_version_command: typing.Optional[builtins.str] = None,
        npm_dist_tag: typing.Optional[builtins.str] = None,
        post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        prerelease: typing.Optional[builtins.str] = None,
        publish_dry_run: typing.Optional[builtins.bool] = None,
        publish_tasks: typing.Optional[builtins.bool] = None,
        releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
        release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
        release_environment: typing.Optional[builtins.str] = None,
        release_every_commit: typing.Optional[builtins.bool] = None,
        release_failure_issue: typing.Optional[builtins.bool] = None,
        release_failure_issue_label: typing.Optional[builtins.str] = None,
        release_schedule: typing.Optional[builtins.str] = None,
        release_tag_prefix: typing.Optional[builtins.str] = None,
        release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
        release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        release_workflow_name: typing.Optional[builtins.str] = None,
        release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        workflow_container_image: typing.Optional[builtins.str] = None,
        workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
        workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
        name: builtins.str,
        commit_generated: typing.Optional[builtins.bool] = None,
        git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
        logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
        outdir: typing.Optional[builtins.str] = None,
        parent: typing.Optional[_Project_57d89203] = None,
        projen_command: typing.Optional[builtins.str] = None,
        projenrc_json: typing.Optional[builtins.bool] = None,
        projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
        renovatebot: typing.Optional[builtins.bool] = None,
        renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param disable_tsconfig: (experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler). Default: false
        :param disable_tsconfig_dev: (experimental) Do not generate a ``tsconfig.dev.json`` file. Default: false
        :param docgen: (experimental) Docgen by Typedoc. Default: false
        :param docs_directory: (experimental) Docs directory. Default: "docs"
        :param entrypoint_types: (experimental) The .d.ts file that includes the type declarations for this module. Default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)
        :param eslint: (experimental) Setup eslint. Default: - true, unless biome is enabled
        :param eslint_options: (experimental) Eslint options. Default: - opinionated default options
        :param libdir: (experimental) Typescript artifacts output directory. Default: "lib"
        :param projenrc_ts: (experimental) Use TypeScript for your projenrc file (``.projenrc.ts``). Default: false
        :param projenrc_ts_options: (experimental) Options for .projenrc.ts.
        :param sample_code: (experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there. Default: true
        :param srcdir: (experimental) Typescript sources directory. Default: "src"
        :param testdir: (experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``. If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``), then tests are going to be compiled into ``lib/`` and executed as javascript. If the test directory is outside of ``src``, then we configure jest to compile the code in-memory. Default: "test"
        :param tsconfig: (experimental) Custom TSConfig. Default: - default options
        :param tsconfig_dev: (experimental) Custom tsconfig options for the development tsconfig.json file (used for testing). Default: - use the production tsconfig options
        :param tsconfig_dev_file: (experimental) The name of the development tsconfig.json file. Default: "tsconfig.dev.json"
        :param ts_jest_options: (experimental) Options for ts-jest.
        :param typescript_version: (experimental) TypeScript version to use. NOTE: Typescript is not semantically versioned and should remain on the same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``). Default: "latest"
        :param default_release_branch: (experimental) The name of the main release branch. Default: "main"
        :param artifacts_directory: (experimental) A directory which will contain build artifacts. Default: "dist"
        :param auto_approve_upgrades: (experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued). Throw if set to true but ``autoApproveOptions`` are not defined. Default: - true
        :param biome: (experimental) Setup Biome. Default: false
        :param biome_options: (experimental) Biome options. Default: - default options
        :param build_workflow: (experimental) Define a GitHub workflow for building PRs. Default: - true if not a subproject
        :param build_workflow_options: (experimental) Options for PR build workflow.
        :param build_workflow_triggers: (deprecated) Build workflow triggers. Default: "{ pullRequest: {}, workflowDispatch: {} }"
        :param bundler_options: (experimental) Options for ``Bundler``.
        :param check_licenses: (experimental) Configure which licenses should be deemed acceptable for use by dependencies. This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered. Default: - no license checks are run during the build and all licenses will be accepted
        :param code_cov: (experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``. Default: false
        :param code_cov_token_secret: (experimental) Define the secret name for a specified https://codecov.io/ token. Default: - OIDC auth is used
        :param copyright_owner: (experimental) License copyright owner. Default: - defaults to the value of authorName or "" if ``authorName`` is undefined.
        :param copyright_period: (experimental) The copyright years to put in the LICENSE file. Default: - current year
        :param dependabot: (experimental) Use dependabot to handle dependency upgrades. Cannot be used in conjunction with ``depsUpgrade``. Default: false
        :param dependabot_options: (experimental) Options for dependabot. Default: - default options
        :param deps_upgrade: (experimental) Use tasks and github workflows to handle dependency upgrades. Cannot be used in conjunction with ``dependabot``. Default: true
        :param deps_upgrade_options: (experimental) Options for ``UpgradeDependencies``. Default: - default options
        :param gitignore: (experimental) Additional entries to .gitignore.
        :param jest: (experimental) Setup jest unit tests. Default: true
        :param jest_options: (experimental) Jest options. Default: - default options
        :param mutable_build: (deprecated) Automatically update files modified during builds to pull-request branches. This means that any files synthesized by projen or e.g. test snapshots will always be up-to-date before a PR is merged. Implies that PR builds do not have anti-tamper checks. Default: true
        :param npmignore: (deprecated) Additional entries to .npmignore.
        :param npmignore_enabled: (experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs. Default: true
        :param npm_ignore_options: (experimental) Configuration options for .npmignore file.
        :param package: (experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``). Default: true
        :param prettier: (experimental) Setup prettier. Default: false
        :param prettier_options: (experimental) Prettier options. Default: - default options
        :param projen_dev_dependency: (experimental) Indicates of "projen" should be installed as a devDependency. Default: - true if not a subproject
        :param projenrc_js: (experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation. Default: - true if projenrcJson is false
        :param projenrc_js_options: (experimental) Options for .projenrc.js. Default: - default options
        :param projen_version: (experimental) Version of projen to install. Default: - Defaults to the latest version.
        :param pull_request_template: (experimental) Include a GitHub pull request template. Default: true
        :param pull_request_template_contents: (experimental) The contents of the pull request template. Default: - default content
        :param release: (experimental) Add release management to this project. Default: - true (false for subprojects)
        :param release_to_npm: (experimental) Automatically release to npm when new versions are introduced. Default: false
        :param release_workflow: (deprecated) DEPRECATED: renamed to ``release``. Default: - true if not a subproject
        :param workflow_bootstrap_steps: (experimental) Workflow steps to use in order to bootstrap this repo. Default: "yarn install --frozen-lockfile && yarn projen"
        :param workflow_git_identity: (experimental) The git identity to use in workflows. Default: - default GitHub Actions user
        :param workflow_node_version: (experimental) The node version used in GitHub Actions workflows. Always use this option if your GitHub Actions workflows require a specific to run. Default: - ``minNodeVersion`` if set, otherwise ``lts/*``.
        :param workflow_package_cache: (experimental) Enable Node.js package cache in GitHub workflows. Default: false
        :param auto_approve_options: (experimental) Enable and configure the 'auto approve' workflow. Default: - auto approve is disabled
        :param auto_merge: (experimental) Enable automatic merging on GitHub. Has no effect if ``github.mergify`` is set to false. Default: true
        :param auto_merge_options: (experimental) Configure options for automatic merging on GitHub. Has no effect if ``github.mergify`` or ``autoMerge`` is set to false. Default: - see defaults in ``AutoMergeOptions``
        :param clobber: (experimental) Add a ``clobber`` task which resets the repo to origin. Default: - true, but false for subprojects
        :param dev_container: (experimental) Add a VSCode development environment (used for GitHub Codespaces). Default: false
        :param github: (experimental) Enable GitHub integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param github_options: (experimental) Options for GitHub integration. Default: - see GitHubOptions
        :param gitpod: (experimental) Add a Gitpod development environment. Default: false
        :param mergify: (deprecated) Whether mergify should be enabled on this repository or not. Default: true
        :param mergify_options: (deprecated) Options for mergify. Default: - default options
        :param project_type: (deprecated) Which type of project this is (library/app). Default: ProjectType.UNKNOWN
        :param projen_credentials: (experimental) Choose a method of providing GitHub API access for projen workflows. Default: - use a personal access token named PROJEN_GITHUB_TOKEN
        :param projen_token_secret: (deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows. This token needs to have the ``repo``, ``workflows`` and ``packages`` scope. Default: "PROJEN_GITHUB_TOKEN"
        :param readme: (experimental) The README setup. Default: - { filename: 'README.md', contents: '# replace this' }
        :param stale: (experimental) Auto-close of stale issues and pull request. See ``staleOptions`` for options. Default: false
        :param stale_options: (experimental) Auto-close stale issues and pull requests. To disable set ``stale`` to ``false``. Default: - see defaults in ``StaleOptions``
        :param vscode: (experimental) Enable VSCode integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param allow_library_dependencies: (experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``. This is normally only allowed for libraries. For apps, there's no meaning for specifying these. Default: true
        :param author_email: (experimental) Author's e-mail.
        :param author_name: (experimental) Author's name.
        :param author_organization: (experimental) Is the author an organization.
        :param author_url: (experimental) Author's URL / Website.
        :param auto_detect_bin: (experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section. Default: true
        :param bin: (experimental) Binary programs vended with your module. You can use this option to add/customize how binaries are represented in your ``package.json``, but unless ``autoDetectBin`` is ``false``, every executable file under ``bin`` will automatically be added to this section.
        :param bugs_email: (experimental) The email address to which issues should be reported.
        :param bugs_url: (experimental) The url to your project's issue tracker.
        :param bundled_deps: (experimental) List of dependencies to bundle into this module. These modules will be added both to the ``dependencies`` section and ``bundledDependencies`` section of your ``package.json``. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include.
        :param bun_version: (experimental) The version of Bun to use if using Bun as a package manager. Default: "latest"
        :param code_artifact_options: (experimental) Options for npm packages using AWS CodeArtifact. This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact Default: - undefined
        :param deps: (experimental) Runtime dependencies of this module. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param description: (experimental) The description is just a string that helps people understand the purpose of the package. It can be used when searching for packages in a package manager as well. See https://classic.yarnpkg.com/en/docs/package-json/#toc-description
        :param dev_deps: (experimental) Build dependencies for this module. These dependencies will only be available in your build environment but will not be fetched when this module is consumed. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param entrypoint: (experimental) Module entrypoint (``main`` in ``package.json``). Set to an empty string to not include ``main`` in your package.json Default: "lib/index.js"
        :param homepage: (experimental) Package's Homepage / Website.
        :param keywords: (experimental) Keywords to include in ``package.json``.
        :param license: (experimental) License's SPDX identifier. See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses. Use the ``licensed`` option if you want to no license to be specified. Default: "Apache-2.0"
        :param licensed: (experimental) Indicates if a license should be added. Default: true
        :param max_node_version: (experimental) The maximum node version supported by this package. Most projects should not use this option. The value indicates that the package is incompatible with any newer versions of node. This requirement is enforced via the engines field. You will normally not need to set this option. Consider this option only if your package is known to not function with newer versions of node. Default: - no maximum version is enforced
        :param min_node_version: (experimental) The minimum node version required by this package to function. Most projects should not use this option. The value indicates that the package is incompatible with any older versions of node. This requirement is enforced via the engines field. You will normally not need to set this option, even if your package is incompatible with EOL versions of node. Consider this option only if your package depends on a specific feature, that is not available in other LTS versions. Setting this option has very high impact on the consumers of your package, as package managers will actively prevent usage with node versions you have marked as incompatible. To change the node version of your CI/CD workflows, use ``workflowNodeVersion``. Default: - no minimum version is enforced
        :param npm_access: (experimental) Access level of the npm package. Default: - for scoped packages (e.g. ``foo@bar``), the default is ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is ``NpmAccess.PUBLIC``.
        :param npm_provenance: (experimental) Should provenance statements be generated when the package is published. A supported package manager is required to publish a package with npm provenance statements and you will need to use a supported CI/CD provider. Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages, which is using npm internally and supports provenance statements independently of the package manager used. Default: - true for public packages, false otherwise
        :param npm_registry: (deprecated) The host name of the npm registry to publish to. Cannot be set together with ``npmRegistryUrl``.
        :param npm_registry_url: (experimental) The base URL of the npm package registry. Must be a URL (e.g. start with "https://" or "http://") Default: "https://registry.npmjs.org"
        :param npm_token_secret: (experimental) GitHub secret which contains the NPM token to use when publishing packages. Default: "NPM_TOKEN"
        :param npm_trusted_publishing: (experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work. Default: - false
        :param package_manager: (experimental) The Node Package Manager used to execute scripts. Default: NodePackageManager.YARN_CLASSIC
        :param package_name: (experimental) The "name" in package.json. Default: - defaults to project name
        :param peer_dependency_options: (experimental) Options for ``peerDeps``.
        :param peer_deps: (experimental) Peer dependencies for this module. Dependencies listed here are required to be installed (and satisfied) by the *consumer* of this library. Using peer dependencies allows you to ensure that only a single module of a certain library exists in the ``node_modules`` tree of your consumers. Note that prior to npm@7, peer dependencies are *not* automatically installed, which means that adding peer dependencies to a library will be a breaking change for your customers. Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is enabled by default), projen will automatically add a dev dependency with a pinned version for each peer dependency. This will ensure that you build & test your module against the lowest peer version required. Default: []
        :param pnpm_version: (experimental) The version of PNPM to use if using PNPM as a package manager. Default: "9"
        :param repository: (experimental) The repository is the location where the actual code for your package lives. See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository
        :param repository_directory: (experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.
        :param scoped_packages_options: (experimental) Options for privately hosted scoped packages. Default: - fetch all scoped packages from the public npm registry
        :param scripts: (deprecated) npm scripts to include. If a script has the same name as a standard script, the standard script will be overwritten. Also adds the script as a task. Default: {}
        :param stability: (experimental) Package's Stability.
        :param yarn_berry_options: (experimental) Options for Yarn Berry. Default: - Yarn Berry v4 with all default options
        :param bump_package: (experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string. This can be any compatible package version, including the deprecated ``standard-version@9``. Default: - A recent version of "commit-and-tag-version"
        :param jsii_release_version: (experimental) Version requirement of ``publib`` which is used to publish modules to npm. Default: "latest"
        :param major_version: (experimental) Major version to release from the default branch. If this is specified, we bump the latest version of this major version line. If not specified, we bump the global latest version. Default: - Major version is not enforced.
        :param min_major_version: (experimental) Minimal Major version to release. This can be useful to set to 1, as breaking changes before the 1.x major release are not incrementing the major version number. Can not be set together with ``majorVersion``. Default: - No minimum version is being enforced
        :param next_version_command: (experimental) A shell command to control the next version to release. If present, this shell command will be run before the bump is executed, and it determines what version to release. It will be executed in the following environment: - Working directory: the project directory. - ``$VERSION``: the current version. Looks like ``1.2.3``. - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset. - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``. The command should print one of the following to ``stdout``: - Nothing: the next version number will be determined based on commit history. - ``x.y.z``: the next version number will be ``x.y.z``. - ``major|minor|patch``: the next version number will be the current version number with the indicated component bumped. This setting cannot be specified together with ``minMajorVersion``; the invoked script can be used to achieve the effects of ``minMajorVersion``. Default: - The next version will be determined based on the commit history and project settings.
        :param npm_dist_tag: (experimental) The npmDistTag to use when publishing from the default branch. To set the npm dist-tag for release branches, set the ``npmDistTag`` property for each branch. Default: "latest"
        :param post_build_steps: (experimental) Steps to execute after build as part of the release workflow. Default: []
        :param prerelease: (experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre"). Default: - normal semantic versions
        :param publish_dry_run: (experimental) Instead of actually publishing to package managers, just print the publishing command. Default: false
        :param publish_tasks: (experimental) Define publishing tasks that can be executed manually as well as workflows. Normally, publishing only happens within automated workflows. Enable this in order to create a publishing task for each publishing activity. Default: false
        :param releasable_commits: (experimental) Find commits that should be considered releasable Used to decide if a release is required. Default: ReleasableCommits.everyCommit()
        :param release_branches: (experimental) Defines additional release branches. A workflow will be created for each release branch which will publish releases from commits in this branch. Each release branch *must* be assigned a major version number which is used to enforce that versions published from that branch always use that major version. If multiple branches are used, the ``majorVersion`` field must also be provided for the default branch. Default: - no additional branches are used for release. you can use ``addBranch()`` to add additional branches.
        :param release_environment: (experimental) The GitHub Actions environment used for the release. This can be used to add an explicit approval step to the release or limit who can initiate a release through environment protection rules. When multiple artifacts are released, the environment can be overwritten on a per artifact basis. Default: - no environment used, unless set at the artifact level
        :param release_every_commit: (deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``. Default: true
        :param release_failure_issue: (experimental) Create a github issue on every failed publishing task. Default: false
        :param release_failure_issue_label: (experimental) The label to apply to issues indicating publish failures. Only applies if ``releaseFailureIssue`` is true. Default: "failed-release"
        :param release_schedule: (deprecated) CRON schedule to trigger new releases. Default: - no scheduled releases
        :param release_tag_prefix: (experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers. Note: this prefix is used to detect the latest tagged version when bumping, so if you change this on a project with an existing version history, you may need to manually tag your latest release with the new prefix. Default: "v"
        :param release_trigger: (experimental) The release trigger to use. Default: - Continuous releases (``ReleaseTrigger.continuous()``)
        :param release_workflow_env: (experimental) Build environment variables for release workflows. Default: {}
        :param release_workflow_name: (experimental) The name of the default release workflow. Default: "release"
        :param release_workflow_setup_steps: (experimental) A set of workflow steps to execute in order to setup the workflow container.
        :param versionrc_options: (experimental) Custom configuration used when creating changelog with commit-and-tag-version package. Given values either append to default configuration or overwrite values in it. Default: - standard configuration applicable for GitHub repositories
        :param workflow_container_image: (experimental) Container image to use for GitHub workflows. Default: - default image
        :param workflow_runs_on: (experimental) Github Runner selection labels. Default: ["ubuntu-latest"]
        :param workflow_runs_on_group: (experimental) Github Runner Group selection options.
        :param name: (experimental) This is the name of your project. Default: $BASEDIR
        :param commit_generated: (experimental) Whether to commit the managed files by default. Default: true
        :param git_ignore_options: (experimental) Configuration options for .gitignore file.
        :param git_options: (experimental) Configuration options for git.
        :param logging: (experimental) Configure logging options such as verbosity. Default: {}
        :param outdir: (experimental) The root directory of the project. Relative to this directory, all files are synthesized. If this project has a parent, this directory is relative to the parent directory and it cannot be the same as the parent or any of it's other subprojects. Default: "."
        :param parent: (experimental) The parent project, if this project is part of a bigger project.
        :param projen_command: (experimental) The shell command to use in order to run the projen CLI. Can be used to customize in special environments. Default: "npx projen"
        :param projenrc_json: (experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation. Default: false
        :param projenrc_json_options: (experimental) Options for .projenrc.json. Default: - default options
        :param renovatebot: (experimental) Use renovatebot to handle dependency upgrades. Default: false
        :param renovatebot_options: (experimental) Options for renovatebot. Default: - default options

        :stability: experimental
        '''
        options = TypeScriptProjectOptions(
            disable_tsconfig=disable_tsconfig,
            disable_tsconfig_dev=disable_tsconfig_dev,
            docgen=docgen,
            docs_directory=docs_directory,
            entrypoint_types=entrypoint_types,
            eslint=eslint,
            eslint_options=eslint_options,
            libdir=libdir,
            projenrc_ts=projenrc_ts,
            projenrc_ts_options=projenrc_ts_options,
            sample_code=sample_code,
            srcdir=srcdir,
            testdir=testdir,
            tsconfig=tsconfig,
            tsconfig_dev=tsconfig_dev,
            tsconfig_dev_file=tsconfig_dev_file,
            ts_jest_options=ts_jest_options,
            typescript_version=typescript_version,
            default_release_branch=default_release_branch,
            artifacts_directory=artifacts_directory,
            auto_approve_upgrades=auto_approve_upgrades,
            biome=biome,
            biome_options=biome_options,
            build_workflow=build_workflow,
            build_workflow_options=build_workflow_options,
            build_workflow_triggers=build_workflow_triggers,
            bundler_options=bundler_options,
            check_licenses=check_licenses,
            code_cov=code_cov,
            code_cov_token_secret=code_cov_token_secret,
            copyright_owner=copyright_owner,
            copyright_period=copyright_period,
            dependabot=dependabot,
            dependabot_options=dependabot_options,
            deps_upgrade=deps_upgrade,
            deps_upgrade_options=deps_upgrade_options,
            gitignore=gitignore,
            jest=jest,
            jest_options=jest_options,
            mutable_build=mutable_build,
            npmignore=npmignore,
            npmignore_enabled=npmignore_enabled,
            npm_ignore_options=npm_ignore_options,
            package=package,
            prettier=prettier,
            prettier_options=prettier_options,
            projen_dev_dependency=projen_dev_dependency,
            projenrc_js=projenrc_js,
            projenrc_js_options=projenrc_js_options,
            projen_version=projen_version,
            pull_request_template=pull_request_template,
            pull_request_template_contents=pull_request_template_contents,
            release=release,
            release_to_npm=release_to_npm,
            release_workflow=release_workflow,
            workflow_bootstrap_steps=workflow_bootstrap_steps,
            workflow_git_identity=workflow_git_identity,
            workflow_node_version=workflow_node_version,
            workflow_package_cache=workflow_package_cache,
            auto_approve_options=auto_approve_options,
            auto_merge=auto_merge,
            auto_merge_options=auto_merge_options,
            clobber=clobber,
            dev_container=dev_container,
            github=github,
            github_options=github_options,
            gitpod=gitpod,
            mergify=mergify,
            mergify_options=mergify_options,
            project_type=project_type,
            projen_credentials=projen_credentials,
            projen_token_secret=projen_token_secret,
            readme=readme,
            stale=stale,
            stale_options=stale_options,
            vscode=vscode,
            allow_library_dependencies=allow_library_dependencies,
            author_email=author_email,
            author_name=author_name,
            author_organization=author_organization,
            author_url=author_url,
            auto_detect_bin=auto_detect_bin,
            bin=bin,
            bugs_email=bugs_email,
            bugs_url=bugs_url,
            bundled_deps=bundled_deps,
            bun_version=bun_version,
            code_artifact_options=code_artifact_options,
            deps=deps,
            description=description,
            dev_deps=dev_deps,
            entrypoint=entrypoint,
            homepage=homepage,
            keywords=keywords,
            license=license,
            licensed=licensed,
            max_node_version=max_node_version,
            min_node_version=min_node_version,
            npm_access=npm_access,
            npm_provenance=npm_provenance,
            npm_registry=npm_registry,
            npm_registry_url=npm_registry_url,
            npm_token_secret=npm_token_secret,
            npm_trusted_publishing=npm_trusted_publishing,
            package_manager=package_manager,
            package_name=package_name,
            peer_dependency_options=peer_dependency_options,
            peer_deps=peer_deps,
            pnpm_version=pnpm_version,
            repository=repository,
            repository_directory=repository_directory,
            scoped_packages_options=scoped_packages_options,
            scripts=scripts,
            stability=stability,
            yarn_berry_options=yarn_berry_options,
            bump_package=bump_package,
            jsii_release_version=jsii_release_version,
            major_version=major_version,
            min_major_version=min_major_version,
            next_version_command=next_version_command,
            npm_dist_tag=npm_dist_tag,
            post_build_steps=post_build_steps,
            prerelease=prerelease,
            publish_dry_run=publish_dry_run,
            publish_tasks=publish_tasks,
            releasable_commits=releasable_commits,
            release_branches=release_branches,
            release_environment=release_environment,
            release_every_commit=release_every_commit,
            release_failure_issue=release_failure_issue,
            release_failure_issue_label=release_failure_issue_label,
            release_schedule=release_schedule,
            release_tag_prefix=release_tag_prefix,
            release_trigger=release_trigger,
            release_workflow_env=release_workflow_env,
            release_workflow_name=release_workflow_name,
            release_workflow_setup_steps=release_workflow_setup_steps,
            versionrc_options=versionrc_options,
            workflow_container_image=workflow_container_image,
            workflow_runs_on=workflow_runs_on,
            workflow_runs_on_group=workflow_runs_on_group,
            name=name,
            commit_generated=commit_generated,
            git_ignore_options=git_ignore_options,
            git_options=git_options,
            logging=logging,
            outdir=outdir,
            parent=parent,
            projen_command=projen_command,
            projenrc_json=projenrc_json,
            projenrc_json_options=projenrc_json_options,
            renovatebot=renovatebot,
            renovatebot_options=renovatebot_options,
        )

        jsii.create(self.__class__, self, [options])

    @jsii.member(jsii_name="defaultTypeScriptCompilerOptions")
    def _default_type_script_compiler_options(
        self,
    ) -> _TypeScriptCompilerOptions_829fc4b0:
        '''(experimental) Projen default Typescript compiler options.

        :stability: experimental
        '''
        return typing.cast(_TypeScriptCompilerOptions_829fc4b0, jsii.invoke(self, "defaultTypeScriptCompilerOptions", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="DEFAULT_TS_JEST_TRANFORM_PATTERN")
    def DEFAULT_TS_JEST_TRANFORM_PATTERN(cls) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.sget(cls, "DEFAULT_TS_JEST_TRANFORM_PATTERN"))

    @builtins.property
    @jsii.member(jsii_name="docsDirectory")
    def docs_directory(self) -> builtins.str:
        '''
        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "docsDirectory"))

    @builtins.property
    @jsii.member(jsii_name="libdir")
    def libdir(self) -> builtins.str:
        '''(experimental) The directory in which compiled .js files reside.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "libdir"))

    @builtins.property
    @jsii.member(jsii_name="srcdir")
    def srcdir(self) -> builtins.str:
        '''(experimental) The directory in which the .ts sources reside.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "srcdir"))

    @builtins.property
    @jsii.member(jsii_name="testdir")
    def testdir(self) -> builtins.str:
        '''(experimental) The directory in which tests reside.

        :stability: experimental
        '''
        return typing.cast(builtins.str, jsii.get(self, "testdir"))

    @builtins.property
    @jsii.member(jsii_name="tsconfigDev")
    def tsconfig_dev(self) -> _TypescriptConfig_e4a2920d:
        '''(experimental) A typescript configuration file which covers all files (sources, tests, projen).

        :stability: experimental
        '''
        return typing.cast(_TypescriptConfig_e4a2920d, jsii.get(self, "tsconfigDev"))

    @builtins.property
    @jsii.member(jsii_name="watchTask")
    def watch_task(self) -> _Task_9fa875b6:
        '''(experimental) The "watch" task.

        :stability: experimental
        '''
        return typing.cast(_Task_9fa875b6, jsii.get(self, "watchTask"))

    @builtins.property
    @jsii.member(jsii_name="docgen")
    def docgen(self) -> typing.Optional[builtins.bool]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "docgen"))

    @builtins.property
    @jsii.member(jsii_name="eslint")
    def eslint(self) -> typing.Optional[_Eslint_b3991f7f]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[_Eslint_b3991f7f], jsii.get(self, "eslint"))

    @builtins.property
    @jsii.member(jsii_name="tsconfig")
    def tsconfig(self) -> typing.Optional[_TypescriptConfig_e4a2920d]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[_TypescriptConfig_e4a2920d], jsii.get(self, "tsconfig"))

    @builtins.property
    @jsii.member(jsii_name="tsconfigEslint")
    def tsconfig_eslint(self) -> typing.Optional[_TypescriptConfig_e4a2920d]:
        '''
        :stability: experimental
        '''
        return typing.cast(typing.Optional[_TypescriptConfig_e4a2920d], jsii.get(self, "tsconfigEslint"))


@jsii.data_type(
    jsii_type="projen.typescript.TypeScriptProjectOptions",
    jsii_struct_bases=[_NodeProjectOptions_d12f6f3b],
    name_mapping={
        "name": "name",
        "commit_generated": "commitGenerated",
        "git_ignore_options": "gitIgnoreOptions",
        "git_options": "gitOptions",
        "logging": "logging",
        "outdir": "outdir",
        "parent": "parent",
        "projen_command": "projenCommand",
        "projenrc_json": "projenrcJson",
        "projenrc_json_options": "projenrcJsonOptions",
        "renovatebot": "renovatebot",
        "renovatebot_options": "renovatebotOptions",
        "auto_approve_options": "autoApproveOptions",
        "auto_merge": "autoMerge",
        "auto_merge_options": "autoMergeOptions",
        "clobber": "clobber",
        "dev_container": "devContainer",
        "github": "github",
        "github_options": "githubOptions",
        "gitpod": "gitpod",
        "mergify": "mergify",
        "mergify_options": "mergifyOptions",
        "project_type": "projectType",
        "projen_credentials": "projenCredentials",
        "projen_token_secret": "projenTokenSecret",
        "readme": "readme",
        "stale": "stale",
        "stale_options": "staleOptions",
        "vscode": "vscode",
        "allow_library_dependencies": "allowLibraryDependencies",
        "author_email": "authorEmail",
        "author_name": "authorName",
        "author_organization": "authorOrganization",
        "author_url": "authorUrl",
        "auto_detect_bin": "autoDetectBin",
        "bin": "bin",
        "bugs_email": "bugsEmail",
        "bugs_url": "bugsUrl",
        "bundled_deps": "bundledDeps",
        "bun_version": "bunVersion",
        "code_artifact_options": "codeArtifactOptions",
        "deps": "deps",
        "description": "description",
        "dev_deps": "devDeps",
        "entrypoint": "entrypoint",
        "homepage": "homepage",
        "keywords": "keywords",
        "license": "license",
        "licensed": "licensed",
        "max_node_version": "maxNodeVersion",
        "min_node_version": "minNodeVersion",
        "npm_access": "npmAccess",
        "npm_provenance": "npmProvenance",
        "npm_registry": "npmRegistry",
        "npm_registry_url": "npmRegistryUrl",
        "npm_token_secret": "npmTokenSecret",
        "npm_trusted_publishing": "npmTrustedPublishing",
        "package_manager": "packageManager",
        "package_name": "packageName",
        "peer_dependency_options": "peerDependencyOptions",
        "peer_deps": "peerDeps",
        "pnpm_version": "pnpmVersion",
        "repository": "repository",
        "repository_directory": "repositoryDirectory",
        "scoped_packages_options": "scopedPackagesOptions",
        "scripts": "scripts",
        "stability": "stability",
        "yarn_berry_options": "yarnBerryOptions",
        "bump_package": "bumpPackage",
        "jsii_release_version": "jsiiReleaseVersion",
        "major_version": "majorVersion",
        "min_major_version": "minMajorVersion",
        "next_version_command": "nextVersionCommand",
        "npm_dist_tag": "npmDistTag",
        "post_build_steps": "postBuildSteps",
        "prerelease": "prerelease",
        "publish_dry_run": "publishDryRun",
        "publish_tasks": "publishTasks",
        "releasable_commits": "releasableCommits",
        "release_branches": "releaseBranches",
        "release_environment": "releaseEnvironment",
        "release_every_commit": "releaseEveryCommit",
        "release_failure_issue": "releaseFailureIssue",
        "release_failure_issue_label": "releaseFailureIssueLabel",
        "release_schedule": "releaseSchedule",
        "release_tag_prefix": "releaseTagPrefix",
        "release_trigger": "releaseTrigger",
        "release_workflow_env": "releaseWorkflowEnv",
        "release_workflow_name": "releaseWorkflowName",
        "release_workflow_setup_steps": "releaseWorkflowSetupSteps",
        "versionrc_options": "versionrcOptions",
        "workflow_container_image": "workflowContainerImage",
        "workflow_runs_on": "workflowRunsOn",
        "workflow_runs_on_group": "workflowRunsOnGroup",
        "default_release_branch": "defaultReleaseBranch",
        "artifacts_directory": "artifactsDirectory",
        "auto_approve_upgrades": "autoApproveUpgrades",
        "biome": "biome",
        "biome_options": "biomeOptions",
        "build_workflow": "buildWorkflow",
        "build_workflow_options": "buildWorkflowOptions",
        "build_workflow_triggers": "buildWorkflowTriggers",
        "bundler_options": "bundlerOptions",
        "check_licenses": "checkLicenses",
        "code_cov": "codeCov",
        "code_cov_token_secret": "codeCovTokenSecret",
        "copyright_owner": "copyrightOwner",
        "copyright_period": "copyrightPeriod",
        "dependabot": "dependabot",
        "dependabot_options": "dependabotOptions",
        "deps_upgrade": "depsUpgrade",
        "deps_upgrade_options": "depsUpgradeOptions",
        "gitignore": "gitignore",
        "jest": "jest",
        "jest_options": "jestOptions",
        "mutable_build": "mutableBuild",
        "npmignore": "npmignore",
        "npmignore_enabled": "npmignoreEnabled",
        "npm_ignore_options": "npmIgnoreOptions",
        "package": "package",
        "prettier": "prettier",
        "prettier_options": "prettierOptions",
        "projen_dev_dependency": "projenDevDependency",
        "projenrc_js": "projenrcJs",
        "projenrc_js_options": "projenrcJsOptions",
        "projen_version": "projenVersion",
        "pull_request_template": "pullRequestTemplate",
        "pull_request_template_contents": "pullRequestTemplateContents",
        "release": "release",
        "release_to_npm": "releaseToNpm",
        "release_workflow": "releaseWorkflow",
        "workflow_bootstrap_steps": "workflowBootstrapSteps",
        "workflow_git_identity": "workflowGitIdentity",
        "workflow_node_version": "workflowNodeVersion",
        "workflow_package_cache": "workflowPackageCache",
        "disable_tsconfig": "disableTsconfig",
        "disable_tsconfig_dev": "disableTsconfigDev",
        "docgen": "docgen",
        "docs_directory": "docsDirectory",
        "entrypoint_types": "entrypointTypes",
        "eslint": "eslint",
        "eslint_options": "eslintOptions",
        "libdir": "libdir",
        "projenrc_ts": "projenrcTs",
        "projenrc_ts_options": "projenrcTsOptions",
        "sample_code": "sampleCode",
        "srcdir": "srcdir",
        "testdir": "testdir",
        "tsconfig": "tsconfig",
        "tsconfig_dev": "tsconfigDev",
        "tsconfig_dev_file": "tsconfigDevFile",
        "ts_jest_options": "tsJestOptions",
        "typescript_version": "typescriptVersion",
    },
)
class TypeScriptProjectOptions(_NodeProjectOptions_d12f6f3b):
    def __init__(
        self,
        *,
        name: builtins.str,
        commit_generated: typing.Optional[builtins.bool] = None,
        git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
        logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
        outdir: typing.Optional[builtins.str] = None,
        parent: typing.Optional[_Project_57d89203] = None,
        projen_command: typing.Optional[builtins.str] = None,
        projenrc_json: typing.Optional[builtins.bool] = None,
        projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
        renovatebot: typing.Optional[builtins.bool] = None,
        renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_merge: typing.Optional[builtins.bool] = None,
        auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
        clobber: typing.Optional[builtins.bool] = None,
        dev_container: typing.Optional[builtins.bool] = None,
        github: typing.Optional[builtins.bool] = None,
        github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
        gitpod: typing.Optional[builtins.bool] = None,
        mergify: typing.Optional[builtins.bool] = None,
        mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
        project_type: typing.Optional[_ProjectType_fd80c725] = None,
        projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
        projen_token_secret: typing.Optional[builtins.str] = None,
        readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
        stale: typing.Optional[builtins.bool] = None,
        stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
        vscode: typing.Optional[builtins.bool] = None,
        allow_library_dependencies: typing.Optional[builtins.bool] = None,
        author_email: typing.Optional[builtins.str] = None,
        author_name: typing.Optional[builtins.str] = None,
        author_organization: typing.Optional[builtins.bool] = None,
        author_url: typing.Optional[builtins.str] = None,
        auto_detect_bin: typing.Optional[builtins.bool] = None,
        bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        bugs_email: typing.Optional[builtins.str] = None,
        bugs_url: typing.Optional[builtins.str] = None,
        bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        bun_version: typing.Optional[builtins.str] = None,
        code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
        deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[builtins.str] = None,
        homepage: typing.Optional[builtins.str] = None,
        keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
        license: typing.Optional[builtins.str] = None,
        licensed: typing.Optional[builtins.bool] = None,
        max_node_version: typing.Optional[builtins.str] = None,
        min_node_version: typing.Optional[builtins.str] = None,
        npm_access: typing.Optional[_NpmAccess_134fa228] = None,
        npm_provenance: typing.Optional[builtins.bool] = None,
        npm_registry: typing.Optional[builtins.str] = None,
        npm_registry_url: typing.Optional[builtins.str] = None,
        npm_token_secret: typing.Optional[builtins.str] = None,
        npm_trusted_publishing: typing.Optional[builtins.bool] = None,
        package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
        package_name: typing.Optional[builtins.str] = None,
        peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
        peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        pnpm_version: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        repository_directory: typing.Optional[builtins.str] = None,
        scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
        scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        stability: typing.Optional[builtins.str] = None,
        yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
        bump_package: typing.Optional[builtins.str] = None,
        jsii_release_version: typing.Optional[builtins.str] = None,
        major_version: typing.Optional[jsii.Number] = None,
        min_major_version: typing.Optional[jsii.Number] = None,
        next_version_command: typing.Optional[builtins.str] = None,
        npm_dist_tag: typing.Optional[builtins.str] = None,
        post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        prerelease: typing.Optional[builtins.str] = None,
        publish_dry_run: typing.Optional[builtins.bool] = None,
        publish_tasks: typing.Optional[builtins.bool] = None,
        releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
        release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
        release_environment: typing.Optional[builtins.str] = None,
        release_every_commit: typing.Optional[builtins.bool] = None,
        release_failure_issue: typing.Optional[builtins.bool] = None,
        release_failure_issue_label: typing.Optional[builtins.str] = None,
        release_schedule: typing.Optional[builtins.str] = None,
        release_tag_prefix: typing.Optional[builtins.str] = None,
        release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
        release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        release_workflow_name: typing.Optional[builtins.str] = None,
        release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        workflow_container_image: typing.Optional[builtins.str] = None,
        workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
        workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
        default_release_branch: builtins.str,
        artifacts_directory: typing.Optional[builtins.str] = None,
        auto_approve_upgrades: typing.Optional[builtins.bool] = None,
        biome: typing.Optional[builtins.bool] = None,
        biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow: typing.Optional[builtins.bool] = None,
        build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
        bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
        check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
        code_cov: typing.Optional[builtins.bool] = None,
        code_cov_token_secret: typing.Optional[builtins.str] = None,
        copyright_owner: typing.Optional[builtins.str] = None,
        copyright_period: typing.Optional[builtins.str] = None,
        dependabot: typing.Optional[builtins.bool] = None,
        dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
        deps_upgrade: typing.Optional[builtins.bool] = None,
        deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
        gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        jest: typing.Optional[builtins.bool] = None,
        jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
        mutable_build: typing.Optional[builtins.bool] = None,
        npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        npmignore_enabled: typing.Optional[builtins.bool] = None,
        npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        package: typing.Optional[builtins.bool] = None,
        prettier: typing.Optional[builtins.bool] = None,
        prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_dev_dependency: typing.Optional[builtins.bool] = None,
        projenrc_js: typing.Optional[builtins.bool] = None,
        projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_version: typing.Optional[builtins.str] = None,
        pull_request_template: typing.Optional[builtins.bool] = None,
        pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
        release: typing.Optional[builtins.bool] = None,
        release_to_npm: typing.Optional[builtins.bool] = None,
        release_workflow: typing.Optional[builtins.bool] = None,
        workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
        workflow_node_version: typing.Optional[builtins.str] = None,
        workflow_package_cache: typing.Optional[builtins.bool] = None,
        disable_tsconfig: typing.Optional[builtins.bool] = None,
        disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
        docgen: typing.Optional[builtins.bool] = None,
        docs_directory: typing.Optional[builtins.str] = None,
        entrypoint_types: typing.Optional[builtins.str] = None,
        eslint: typing.Optional[builtins.bool] = None,
        eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
        libdir: typing.Optional[builtins.str] = None,
        projenrc_ts: typing.Optional[builtins.bool] = None,
        projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        sample_code: typing.Optional[builtins.bool] = None,
        srcdir: typing.Optional[builtins.str] = None,
        testdir: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev_file: typing.Optional[builtins.str] = None,
        ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        typescript_version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param name: (experimental) This is the name of your project. Default: $BASEDIR
        :param commit_generated: (experimental) Whether to commit the managed files by default. Default: true
        :param git_ignore_options: (experimental) Configuration options for .gitignore file.
        :param git_options: (experimental) Configuration options for git.
        :param logging: (experimental) Configure logging options such as verbosity. Default: {}
        :param outdir: (experimental) The root directory of the project. Relative to this directory, all files are synthesized. If this project has a parent, this directory is relative to the parent directory and it cannot be the same as the parent or any of it's other subprojects. Default: "."
        :param parent: (experimental) The parent project, if this project is part of a bigger project.
        :param projen_command: (experimental) The shell command to use in order to run the projen CLI. Can be used to customize in special environments. Default: "npx projen"
        :param projenrc_json: (experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation. Default: false
        :param projenrc_json_options: (experimental) Options for .projenrc.json. Default: - default options
        :param renovatebot: (experimental) Use renovatebot to handle dependency upgrades. Default: false
        :param renovatebot_options: (experimental) Options for renovatebot. Default: - default options
        :param auto_approve_options: (experimental) Enable and configure the 'auto approve' workflow. Default: - auto approve is disabled
        :param auto_merge: (experimental) Enable automatic merging on GitHub. Has no effect if ``github.mergify`` is set to false. Default: true
        :param auto_merge_options: (experimental) Configure options for automatic merging on GitHub. Has no effect if ``github.mergify`` or ``autoMerge`` is set to false. Default: - see defaults in ``AutoMergeOptions``
        :param clobber: (experimental) Add a ``clobber`` task which resets the repo to origin. Default: - true, but false for subprojects
        :param dev_container: (experimental) Add a VSCode development environment (used for GitHub Codespaces). Default: false
        :param github: (experimental) Enable GitHub integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param github_options: (experimental) Options for GitHub integration. Default: - see GitHubOptions
        :param gitpod: (experimental) Add a Gitpod development environment. Default: false
        :param mergify: (deprecated) Whether mergify should be enabled on this repository or not. Default: true
        :param mergify_options: (deprecated) Options for mergify. Default: - default options
        :param project_type: (deprecated) Which type of project this is (library/app). Default: ProjectType.UNKNOWN
        :param projen_credentials: (experimental) Choose a method of providing GitHub API access for projen workflows. Default: - use a personal access token named PROJEN_GITHUB_TOKEN
        :param projen_token_secret: (deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows. This token needs to have the ``repo``, ``workflows`` and ``packages`` scope. Default: "PROJEN_GITHUB_TOKEN"
        :param readme: (experimental) The README setup. Default: - { filename: 'README.md', contents: '# replace this' }
        :param stale: (experimental) Auto-close of stale issues and pull request. See ``staleOptions`` for options. Default: false
        :param stale_options: (experimental) Auto-close stale issues and pull requests. To disable set ``stale`` to ``false``. Default: - see defaults in ``StaleOptions``
        :param vscode: (experimental) Enable VSCode integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param allow_library_dependencies: (experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``. This is normally only allowed for libraries. For apps, there's no meaning for specifying these. Default: true
        :param author_email: (experimental) Author's e-mail.
        :param author_name: (experimental) Author's name.
        :param author_organization: (experimental) Is the author an organization.
        :param author_url: (experimental) Author's URL / Website.
        :param auto_detect_bin: (experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section. Default: true
        :param bin: (experimental) Binary programs vended with your module. You can use this option to add/customize how binaries are represented in your ``package.json``, but unless ``autoDetectBin`` is ``false``, every executable file under ``bin`` will automatically be added to this section.
        :param bugs_email: (experimental) The email address to which issues should be reported.
        :param bugs_url: (experimental) The url to your project's issue tracker.
        :param bundled_deps: (experimental) List of dependencies to bundle into this module. These modules will be added both to the ``dependencies`` section and ``bundledDependencies`` section of your ``package.json``. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include.
        :param bun_version: (experimental) The version of Bun to use if using Bun as a package manager. Default: "latest"
        :param code_artifact_options: (experimental) Options for npm packages using AWS CodeArtifact. This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact Default: - undefined
        :param deps: (experimental) Runtime dependencies of this module. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param description: (experimental) The description is just a string that helps people understand the purpose of the package. It can be used when searching for packages in a package manager as well. See https://classic.yarnpkg.com/en/docs/package-json/#toc-description
        :param dev_deps: (experimental) Build dependencies for this module. These dependencies will only be available in your build environment but will not be fetched when this module is consumed. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param entrypoint: (experimental) Module entrypoint (``main`` in ``package.json``). Set to an empty string to not include ``main`` in your package.json Default: "lib/index.js"
        :param homepage: (experimental) Package's Homepage / Website.
        :param keywords: (experimental) Keywords to include in ``package.json``.
        :param license: (experimental) License's SPDX identifier. See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses. Use the ``licensed`` option if you want to no license to be specified. Default: "Apache-2.0"
        :param licensed: (experimental) Indicates if a license should be added. Default: true
        :param max_node_version: (experimental) The maximum node version supported by this package. Most projects should not use this option. The value indicates that the package is incompatible with any newer versions of node. This requirement is enforced via the engines field. You will normally not need to set this option. Consider this option only if your package is known to not function with newer versions of node. Default: - no maximum version is enforced
        :param min_node_version: (experimental) The minimum node version required by this package to function. Most projects should not use this option. The value indicates that the package is incompatible with any older versions of node. This requirement is enforced via the engines field. You will normally not need to set this option, even if your package is incompatible with EOL versions of node. Consider this option only if your package depends on a specific feature, that is not available in other LTS versions. Setting this option has very high impact on the consumers of your package, as package managers will actively prevent usage with node versions you have marked as incompatible. To change the node version of your CI/CD workflows, use ``workflowNodeVersion``. Default: - no minimum version is enforced
        :param npm_access: (experimental) Access level of the npm package. Default: - for scoped packages (e.g. ``foo@bar``), the default is ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is ``NpmAccess.PUBLIC``.
        :param npm_provenance: (experimental) Should provenance statements be generated when the package is published. A supported package manager is required to publish a package with npm provenance statements and you will need to use a supported CI/CD provider. Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages, which is using npm internally and supports provenance statements independently of the package manager used. Default: - true for public packages, false otherwise
        :param npm_registry: (deprecated) The host name of the npm registry to publish to. Cannot be set together with ``npmRegistryUrl``.
        :param npm_registry_url: (experimental) The base URL of the npm package registry. Must be a URL (e.g. start with "https://" or "http://") Default: "https://registry.npmjs.org"
        :param npm_token_secret: (experimental) GitHub secret which contains the NPM token to use when publishing packages. Default: "NPM_TOKEN"
        :param npm_trusted_publishing: (experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work. Default: - false
        :param package_manager: (experimental) The Node Package Manager used to execute scripts. Default: NodePackageManager.YARN_CLASSIC
        :param package_name: (experimental) The "name" in package.json. Default: - defaults to project name
        :param peer_dependency_options: (experimental) Options for ``peerDeps``.
        :param peer_deps: (experimental) Peer dependencies for this module. Dependencies listed here are required to be installed (and satisfied) by the *consumer* of this library. Using peer dependencies allows you to ensure that only a single module of a certain library exists in the ``node_modules`` tree of your consumers. Note that prior to npm@7, peer dependencies are *not* automatically installed, which means that adding peer dependencies to a library will be a breaking change for your customers. Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is enabled by default), projen will automatically add a dev dependency with a pinned version for each peer dependency. This will ensure that you build & test your module against the lowest peer version required. Default: []
        :param pnpm_version: (experimental) The version of PNPM to use if using PNPM as a package manager. Default: "9"
        :param repository: (experimental) The repository is the location where the actual code for your package lives. See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository
        :param repository_directory: (experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.
        :param scoped_packages_options: (experimental) Options for privately hosted scoped packages. Default: - fetch all scoped packages from the public npm registry
        :param scripts: (deprecated) npm scripts to include. If a script has the same name as a standard script, the standard script will be overwritten. Also adds the script as a task. Default: {}
        :param stability: (experimental) Package's Stability.
        :param yarn_berry_options: (experimental) Options for Yarn Berry. Default: - Yarn Berry v4 with all default options
        :param bump_package: (experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string. This can be any compatible package version, including the deprecated ``standard-version@9``. Default: - A recent version of "commit-and-tag-version"
        :param jsii_release_version: (experimental) Version requirement of ``publib`` which is used to publish modules to npm. Default: "latest"
        :param major_version: (experimental) Major version to release from the default branch. If this is specified, we bump the latest version of this major version line. If not specified, we bump the global latest version. Default: - Major version is not enforced.
        :param min_major_version: (experimental) Minimal Major version to release. This can be useful to set to 1, as breaking changes before the 1.x major release are not incrementing the major version number. Can not be set together with ``majorVersion``. Default: - No minimum version is being enforced
        :param next_version_command: (experimental) A shell command to control the next version to release. If present, this shell command will be run before the bump is executed, and it determines what version to release. It will be executed in the following environment: - Working directory: the project directory. - ``$VERSION``: the current version. Looks like ``1.2.3``. - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset. - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``. The command should print one of the following to ``stdout``: - Nothing: the next version number will be determined based on commit history. - ``x.y.z``: the next version number will be ``x.y.z``. - ``major|minor|patch``: the next version number will be the current version number with the indicated component bumped. This setting cannot be specified together with ``minMajorVersion``; the invoked script can be used to achieve the effects of ``minMajorVersion``. Default: - The next version will be determined based on the commit history and project settings.
        :param npm_dist_tag: (experimental) The npmDistTag to use when publishing from the default branch. To set the npm dist-tag for release branches, set the ``npmDistTag`` property for each branch. Default: "latest"
        :param post_build_steps: (experimental) Steps to execute after build as part of the release workflow. Default: []
        :param prerelease: (experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre"). Default: - normal semantic versions
        :param publish_dry_run: (experimental) Instead of actually publishing to package managers, just print the publishing command. Default: false
        :param publish_tasks: (experimental) Define publishing tasks that can be executed manually as well as workflows. Normally, publishing only happens within automated workflows. Enable this in order to create a publishing task for each publishing activity. Default: false
        :param releasable_commits: (experimental) Find commits that should be considered releasable Used to decide if a release is required. Default: ReleasableCommits.everyCommit()
        :param release_branches: (experimental) Defines additional release branches. A workflow will be created for each release branch which will publish releases from commits in this branch. Each release branch *must* be assigned a major version number which is used to enforce that versions published from that branch always use that major version. If multiple branches are used, the ``majorVersion`` field must also be provided for the default branch. Default: - no additional branches are used for release. you can use ``addBranch()`` to add additional branches.
        :param release_environment: (experimental) The GitHub Actions environment used for the release. This can be used to add an explicit approval step to the release or limit who can initiate a release through environment protection rules. When multiple artifacts are released, the environment can be overwritten on a per artifact basis. Default: - no environment used, unless set at the artifact level
        :param release_every_commit: (deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``. Default: true
        :param release_failure_issue: (experimental) Create a github issue on every failed publishing task. Default: false
        :param release_failure_issue_label: (experimental) The label to apply to issues indicating publish failures. Only applies if ``releaseFailureIssue`` is true. Default: "failed-release"
        :param release_schedule: (deprecated) CRON schedule to trigger new releases. Default: - no scheduled releases
        :param release_tag_prefix: (experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers. Note: this prefix is used to detect the latest tagged version when bumping, so if you change this on a project with an existing version history, you may need to manually tag your latest release with the new prefix. Default: "v"
        :param release_trigger: (experimental) The release trigger to use. Default: - Continuous releases (``ReleaseTrigger.continuous()``)
        :param release_workflow_env: (experimental) Build environment variables for release workflows. Default: {}
        :param release_workflow_name: (experimental) The name of the default release workflow. Default: "release"
        :param release_workflow_setup_steps: (experimental) A set of workflow steps to execute in order to setup the workflow container.
        :param versionrc_options: (experimental) Custom configuration used when creating changelog with commit-and-tag-version package. Given values either append to default configuration or overwrite values in it. Default: - standard configuration applicable for GitHub repositories
        :param workflow_container_image: (experimental) Container image to use for GitHub workflows. Default: - default image
        :param workflow_runs_on: (experimental) Github Runner selection labels. Default: ["ubuntu-latest"]
        :param workflow_runs_on_group: (experimental) Github Runner Group selection options.
        :param default_release_branch: (experimental) The name of the main release branch. Default: "main"
        :param artifacts_directory: (experimental) A directory which will contain build artifacts. Default: "dist"
        :param auto_approve_upgrades: (experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued). Throw if set to true but ``autoApproveOptions`` are not defined. Default: - true
        :param biome: (experimental) Setup Biome. Default: false
        :param biome_options: (experimental) Biome options. Default: - default options
        :param build_workflow: (experimental) Define a GitHub workflow for building PRs. Default: - true if not a subproject
        :param build_workflow_options: (experimental) Options for PR build workflow.
        :param build_workflow_triggers: (deprecated) Build workflow triggers. Default: "{ pullRequest: {}, workflowDispatch: {} }"
        :param bundler_options: (experimental) Options for ``Bundler``.
        :param check_licenses: (experimental) Configure which licenses should be deemed acceptable for use by dependencies. This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered. Default: - no license checks are run during the build and all licenses will be accepted
        :param code_cov: (experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``. Default: false
        :param code_cov_token_secret: (experimental) Define the secret name for a specified https://codecov.io/ token. Default: - OIDC auth is used
        :param copyright_owner: (experimental) License copyright owner. Default: - defaults to the value of authorName or "" if ``authorName`` is undefined.
        :param copyright_period: (experimental) The copyright years to put in the LICENSE file. Default: - current year
        :param dependabot: (experimental) Use dependabot to handle dependency upgrades. Cannot be used in conjunction with ``depsUpgrade``. Default: false
        :param dependabot_options: (experimental) Options for dependabot. Default: - default options
        :param deps_upgrade: (experimental) Use tasks and github workflows to handle dependency upgrades. Cannot be used in conjunction with ``dependabot``. Default: true
        :param deps_upgrade_options: (experimental) Options for ``UpgradeDependencies``. Default: - default options
        :param gitignore: (experimental) Additional entries to .gitignore.
        :param jest: (experimental) Setup jest unit tests. Default: true
        :param jest_options: (experimental) Jest options. Default: - default options
        :param mutable_build: (deprecated) Automatically update files modified during builds to pull-request branches. This means that any files synthesized by projen or e.g. test snapshots will always be up-to-date before a PR is merged. Implies that PR builds do not have anti-tamper checks. Default: true
        :param npmignore: (deprecated) Additional entries to .npmignore.
        :param npmignore_enabled: (experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs. Default: true
        :param npm_ignore_options: (experimental) Configuration options for .npmignore file.
        :param package: (experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``). Default: true
        :param prettier: (experimental) Setup prettier. Default: false
        :param prettier_options: (experimental) Prettier options. Default: - default options
        :param projen_dev_dependency: (experimental) Indicates of "projen" should be installed as a devDependency. Default: - true if not a subproject
        :param projenrc_js: (experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation. Default: - true if projenrcJson is false
        :param projenrc_js_options: (experimental) Options for .projenrc.js. Default: - default options
        :param projen_version: (experimental) Version of projen to install. Default: - Defaults to the latest version.
        :param pull_request_template: (experimental) Include a GitHub pull request template. Default: true
        :param pull_request_template_contents: (experimental) The contents of the pull request template. Default: - default content
        :param release: (experimental) Add release management to this project. Default: - true (false for subprojects)
        :param release_to_npm: (experimental) Automatically release to npm when new versions are introduced. Default: false
        :param release_workflow: (deprecated) DEPRECATED: renamed to ``release``. Default: - true if not a subproject
        :param workflow_bootstrap_steps: (experimental) Workflow steps to use in order to bootstrap this repo. Default: "yarn install --frozen-lockfile && yarn projen"
        :param workflow_git_identity: (experimental) The git identity to use in workflows. Default: - default GitHub Actions user
        :param workflow_node_version: (experimental) The node version used in GitHub Actions workflows. Always use this option if your GitHub Actions workflows require a specific to run. Default: - ``minNodeVersion`` if set, otherwise ``lts/*``.
        :param workflow_package_cache: (experimental) Enable Node.js package cache in GitHub workflows. Default: false
        :param disable_tsconfig: (experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler). Default: false
        :param disable_tsconfig_dev: (experimental) Do not generate a ``tsconfig.dev.json`` file. Default: false
        :param docgen: (experimental) Docgen by Typedoc. Default: false
        :param docs_directory: (experimental) Docs directory. Default: "docs"
        :param entrypoint_types: (experimental) The .d.ts file that includes the type declarations for this module. Default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)
        :param eslint: (experimental) Setup eslint. Default: - true, unless biome is enabled
        :param eslint_options: (experimental) Eslint options. Default: - opinionated default options
        :param libdir: (experimental) Typescript artifacts output directory. Default: "lib"
        :param projenrc_ts: (experimental) Use TypeScript for your projenrc file (``.projenrc.ts``). Default: false
        :param projenrc_ts_options: (experimental) Options for .projenrc.ts.
        :param sample_code: (experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there. Default: true
        :param srcdir: (experimental) Typescript sources directory. Default: "src"
        :param testdir: (experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``. If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``), then tests are going to be compiled into ``lib/`` and executed as javascript. If the test directory is outside of ``src``, then we configure jest to compile the code in-memory. Default: "test"
        :param tsconfig: (experimental) Custom TSConfig. Default: - default options
        :param tsconfig_dev: (experimental) Custom tsconfig options for the development tsconfig.json file (used for testing). Default: - use the production tsconfig options
        :param tsconfig_dev_file: (experimental) The name of the development tsconfig.json file. Default: "tsconfig.dev.json"
        :param ts_jest_options: (experimental) Options for ts-jest.
        :param typescript_version: (experimental) TypeScript version to use. NOTE: Typescript is not semantically versioned and should remain on the same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``). Default: "latest"

        :stability: experimental
        '''
        if isinstance(git_ignore_options, dict):
            git_ignore_options = _IgnoreFileOptions_86c48b91(**git_ignore_options)
        if isinstance(git_options, dict):
            git_options = _GitOptions_a65916a3(**git_options)
        if isinstance(logging, dict):
            logging = _LoggerOptions_eb0f6309(**logging)
        if isinstance(projenrc_json_options, dict):
            projenrc_json_options = _ProjenrcJsonOptions_9c40dd4f(**projenrc_json_options)
        if isinstance(renovatebot_options, dict):
            renovatebot_options = _RenovatebotOptions_18e6b8a1(**renovatebot_options)
        if isinstance(auto_approve_options, dict):
            auto_approve_options = _AutoApproveOptions_dac86cbe(**auto_approve_options)
        if isinstance(auto_merge_options, dict):
            auto_merge_options = _AutoMergeOptions_d112cd3c(**auto_merge_options)
        if isinstance(github_options, dict):
            github_options = _GitHubOptions_21553699(**github_options)
        if isinstance(mergify_options, dict):
            mergify_options = _MergifyOptions_a6faaab3(**mergify_options)
        if isinstance(readme, dict):
            readme = _SampleReadmeProps_3518b03b(**readme)
        if isinstance(stale_options, dict):
            stale_options = _StaleOptions_929db764(**stale_options)
        if isinstance(code_artifact_options, dict):
            code_artifact_options = _CodeArtifactOptions_e4782b3e(**code_artifact_options)
        if isinstance(peer_dependency_options, dict):
            peer_dependency_options = _PeerDependencyOptions_99d7d493(**peer_dependency_options)
        if isinstance(yarn_berry_options, dict):
            yarn_berry_options = _YarnBerryOptions_b6942539(**yarn_berry_options)
        if isinstance(workflow_runs_on_group, dict):
            workflow_runs_on_group = _GroupRunnerOptions_148c59c1(**workflow_runs_on_group)
        if isinstance(biome_options, dict):
            biome_options = _BiomeOptions_452ab984(**biome_options)
        if isinstance(build_workflow_options, dict):
            build_workflow_options = _BuildWorkflowOptions_b756f97f(**build_workflow_options)
        if isinstance(build_workflow_triggers, dict):
            build_workflow_triggers = _Triggers_e9ae7617(**build_workflow_triggers)
        if isinstance(bundler_options, dict):
            bundler_options = _BundlerOptions_d60b85ed(**bundler_options)
        if isinstance(check_licenses, dict):
            check_licenses = _LicenseCheckerOptions_80bcd362(**check_licenses)
        if isinstance(dependabot_options, dict):
            dependabot_options = _DependabotOptions_0cedc635(**dependabot_options)
        if isinstance(deps_upgrade_options, dict):
            deps_upgrade_options = _UpgradeDependenciesOptions_1d8ce4da(**deps_upgrade_options)
        if isinstance(jest_options, dict):
            jest_options = _JestOptions_a085f64e(**jest_options)
        if isinstance(npm_ignore_options, dict):
            npm_ignore_options = _IgnoreFileOptions_86c48b91(**npm_ignore_options)
        if isinstance(prettier_options, dict):
            prettier_options = _PrettierOptions_41a5f203(**prettier_options)
        if isinstance(projenrc_js_options, dict):
            projenrc_js_options = _ProjenrcOptions_179dd39f(**projenrc_js_options)
        if isinstance(workflow_git_identity, dict):
            workflow_git_identity = _GitIdentity_6effc3de(**workflow_git_identity)
        if isinstance(eslint_options, dict):
            eslint_options = _EslintOptions_824f60bb(**eslint_options)
        if isinstance(projenrc_ts_options, dict):
            projenrc_ts_options = ProjenrcOptions(**projenrc_ts_options)
        if isinstance(tsconfig, dict):
            tsconfig = _TypescriptConfigOptions_8c5492cd(**tsconfig)
        if isinstance(tsconfig_dev, dict):
            tsconfig_dev = _TypescriptConfigOptions_8c5492cd(**tsconfig_dev)
        if isinstance(ts_jest_options, dict):
            ts_jest_options = TsJestOptions(**ts_jest_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a914f27f5d915b07b8847d407b03b08cab2aad7b213973084a9026526734c711)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument commit_generated", value=commit_generated, expected_type=type_hints["commit_generated"])
            check_type(argname="argument git_ignore_options", value=git_ignore_options, expected_type=type_hints["git_ignore_options"])
            check_type(argname="argument git_options", value=git_options, expected_type=type_hints["git_options"])
            check_type(argname="argument logging", value=logging, expected_type=type_hints["logging"])
            check_type(argname="argument outdir", value=outdir, expected_type=type_hints["outdir"])
            check_type(argname="argument parent", value=parent, expected_type=type_hints["parent"])
            check_type(argname="argument projen_command", value=projen_command, expected_type=type_hints["projen_command"])
            check_type(argname="argument projenrc_json", value=projenrc_json, expected_type=type_hints["projenrc_json"])
            check_type(argname="argument projenrc_json_options", value=projenrc_json_options, expected_type=type_hints["projenrc_json_options"])
            check_type(argname="argument renovatebot", value=renovatebot, expected_type=type_hints["renovatebot"])
            check_type(argname="argument renovatebot_options", value=renovatebot_options, expected_type=type_hints["renovatebot_options"])
            check_type(argname="argument auto_approve_options", value=auto_approve_options, expected_type=type_hints["auto_approve_options"])
            check_type(argname="argument auto_merge", value=auto_merge, expected_type=type_hints["auto_merge"])
            check_type(argname="argument auto_merge_options", value=auto_merge_options, expected_type=type_hints["auto_merge_options"])
            check_type(argname="argument clobber", value=clobber, expected_type=type_hints["clobber"])
            check_type(argname="argument dev_container", value=dev_container, expected_type=type_hints["dev_container"])
            check_type(argname="argument github", value=github, expected_type=type_hints["github"])
            check_type(argname="argument github_options", value=github_options, expected_type=type_hints["github_options"])
            check_type(argname="argument gitpod", value=gitpod, expected_type=type_hints["gitpod"])
            check_type(argname="argument mergify", value=mergify, expected_type=type_hints["mergify"])
            check_type(argname="argument mergify_options", value=mergify_options, expected_type=type_hints["mergify_options"])
            check_type(argname="argument project_type", value=project_type, expected_type=type_hints["project_type"])
            check_type(argname="argument projen_credentials", value=projen_credentials, expected_type=type_hints["projen_credentials"])
            check_type(argname="argument projen_token_secret", value=projen_token_secret, expected_type=type_hints["projen_token_secret"])
            check_type(argname="argument readme", value=readme, expected_type=type_hints["readme"])
            check_type(argname="argument stale", value=stale, expected_type=type_hints["stale"])
            check_type(argname="argument stale_options", value=stale_options, expected_type=type_hints["stale_options"])
            check_type(argname="argument vscode", value=vscode, expected_type=type_hints["vscode"])
            check_type(argname="argument allow_library_dependencies", value=allow_library_dependencies, expected_type=type_hints["allow_library_dependencies"])
            check_type(argname="argument author_email", value=author_email, expected_type=type_hints["author_email"])
            check_type(argname="argument author_name", value=author_name, expected_type=type_hints["author_name"])
            check_type(argname="argument author_organization", value=author_organization, expected_type=type_hints["author_organization"])
            check_type(argname="argument author_url", value=author_url, expected_type=type_hints["author_url"])
            check_type(argname="argument auto_detect_bin", value=auto_detect_bin, expected_type=type_hints["auto_detect_bin"])
            check_type(argname="argument bin", value=bin, expected_type=type_hints["bin"])
            check_type(argname="argument bugs_email", value=bugs_email, expected_type=type_hints["bugs_email"])
            check_type(argname="argument bugs_url", value=bugs_url, expected_type=type_hints["bugs_url"])
            check_type(argname="argument bundled_deps", value=bundled_deps, expected_type=type_hints["bundled_deps"])
            check_type(argname="argument bun_version", value=bun_version, expected_type=type_hints["bun_version"])
            check_type(argname="argument code_artifact_options", value=code_artifact_options, expected_type=type_hints["code_artifact_options"])
            check_type(argname="argument deps", value=deps, expected_type=type_hints["deps"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument dev_deps", value=dev_deps, expected_type=type_hints["dev_deps"])
            check_type(argname="argument entrypoint", value=entrypoint, expected_type=type_hints["entrypoint"])
            check_type(argname="argument homepage", value=homepage, expected_type=type_hints["homepage"])
            check_type(argname="argument keywords", value=keywords, expected_type=type_hints["keywords"])
            check_type(argname="argument license", value=license, expected_type=type_hints["license"])
            check_type(argname="argument licensed", value=licensed, expected_type=type_hints["licensed"])
            check_type(argname="argument max_node_version", value=max_node_version, expected_type=type_hints["max_node_version"])
            check_type(argname="argument min_node_version", value=min_node_version, expected_type=type_hints["min_node_version"])
            check_type(argname="argument npm_access", value=npm_access, expected_type=type_hints["npm_access"])
            check_type(argname="argument npm_provenance", value=npm_provenance, expected_type=type_hints["npm_provenance"])
            check_type(argname="argument npm_registry", value=npm_registry, expected_type=type_hints["npm_registry"])
            check_type(argname="argument npm_registry_url", value=npm_registry_url, expected_type=type_hints["npm_registry_url"])
            check_type(argname="argument npm_token_secret", value=npm_token_secret, expected_type=type_hints["npm_token_secret"])
            check_type(argname="argument npm_trusted_publishing", value=npm_trusted_publishing, expected_type=type_hints["npm_trusted_publishing"])
            check_type(argname="argument package_manager", value=package_manager, expected_type=type_hints["package_manager"])
            check_type(argname="argument package_name", value=package_name, expected_type=type_hints["package_name"])
            check_type(argname="argument peer_dependency_options", value=peer_dependency_options, expected_type=type_hints["peer_dependency_options"])
            check_type(argname="argument peer_deps", value=peer_deps, expected_type=type_hints["peer_deps"])
            check_type(argname="argument pnpm_version", value=pnpm_version, expected_type=type_hints["pnpm_version"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument repository_directory", value=repository_directory, expected_type=type_hints["repository_directory"])
            check_type(argname="argument scoped_packages_options", value=scoped_packages_options, expected_type=type_hints["scoped_packages_options"])
            check_type(argname="argument scripts", value=scripts, expected_type=type_hints["scripts"])
            check_type(argname="argument stability", value=stability, expected_type=type_hints["stability"])
            check_type(argname="argument yarn_berry_options", value=yarn_berry_options, expected_type=type_hints["yarn_berry_options"])
            check_type(argname="argument bump_package", value=bump_package, expected_type=type_hints["bump_package"])
            check_type(argname="argument jsii_release_version", value=jsii_release_version, expected_type=type_hints["jsii_release_version"])
            check_type(argname="argument major_version", value=major_version, expected_type=type_hints["major_version"])
            check_type(argname="argument min_major_version", value=min_major_version, expected_type=type_hints["min_major_version"])
            check_type(argname="argument next_version_command", value=next_version_command, expected_type=type_hints["next_version_command"])
            check_type(argname="argument npm_dist_tag", value=npm_dist_tag, expected_type=type_hints["npm_dist_tag"])
            check_type(argname="argument post_build_steps", value=post_build_steps, expected_type=type_hints["post_build_steps"])
            check_type(argname="argument prerelease", value=prerelease, expected_type=type_hints["prerelease"])
            check_type(argname="argument publish_dry_run", value=publish_dry_run, expected_type=type_hints["publish_dry_run"])
            check_type(argname="argument publish_tasks", value=publish_tasks, expected_type=type_hints["publish_tasks"])
            check_type(argname="argument releasable_commits", value=releasable_commits, expected_type=type_hints["releasable_commits"])
            check_type(argname="argument release_branches", value=release_branches, expected_type=type_hints["release_branches"])
            check_type(argname="argument release_environment", value=release_environment, expected_type=type_hints["release_environment"])
            check_type(argname="argument release_every_commit", value=release_every_commit, expected_type=type_hints["release_every_commit"])
            check_type(argname="argument release_failure_issue", value=release_failure_issue, expected_type=type_hints["release_failure_issue"])
            check_type(argname="argument release_failure_issue_label", value=release_failure_issue_label, expected_type=type_hints["release_failure_issue_label"])
            check_type(argname="argument release_schedule", value=release_schedule, expected_type=type_hints["release_schedule"])
            check_type(argname="argument release_tag_prefix", value=release_tag_prefix, expected_type=type_hints["release_tag_prefix"])
            check_type(argname="argument release_trigger", value=release_trigger, expected_type=type_hints["release_trigger"])
            check_type(argname="argument release_workflow_env", value=release_workflow_env, expected_type=type_hints["release_workflow_env"])
            check_type(argname="argument release_workflow_name", value=release_workflow_name, expected_type=type_hints["release_workflow_name"])
            check_type(argname="argument release_workflow_setup_steps", value=release_workflow_setup_steps, expected_type=type_hints["release_workflow_setup_steps"])
            check_type(argname="argument versionrc_options", value=versionrc_options, expected_type=type_hints["versionrc_options"])
            check_type(argname="argument workflow_container_image", value=workflow_container_image, expected_type=type_hints["workflow_container_image"])
            check_type(argname="argument workflow_runs_on", value=workflow_runs_on, expected_type=type_hints["workflow_runs_on"])
            check_type(argname="argument workflow_runs_on_group", value=workflow_runs_on_group, expected_type=type_hints["workflow_runs_on_group"])
            check_type(argname="argument default_release_branch", value=default_release_branch, expected_type=type_hints["default_release_branch"])
            check_type(argname="argument artifacts_directory", value=artifacts_directory, expected_type=type_hints["artifacts_directory"])
            check_type(argname="argument auto_approve_upgrades", value=auto_approve_upgrades, expected_type=type_hints["auto_approve_upgrades"])
            check_type(argname="argument biome", value=biome, expected_type=type_hints["biome"])
            check_type(argname="argument biome_options", value=biome_options, expected_type=type_hints["biome_options"])
            check_type(argname="argument build_workflow", value=build_workflow, expected_type=type_hints["build_workflow"])
            check_type(argname="argument build_workflow_options", value=build_workflow_options, expected_type=type_hints["build_workflow_options"])
            check_type(argname="argument build_workflow_triggers", value=build_workflow_triggers, expected_type=type_hints["build_workflow_triggers"])
            check_type(argname="argument bundler_options", value=bundler_options, expected_type=type_hints["bundler_options"])
            check_type(argname="argument check_licenses", value=check_licenses, expected_type=type_hints["check_licenses"])
            check_type(argname="argument code_cov", value=code_cov, expected_type=type_hints["code_cov"])
            check_type(argname="argument code_cov_token_secret", value=code_cov_token_secret, expected_type=type_hints["code_cov_token_secret"])
            check_type(argname="argument copyright_owner", value=copyright_owner, expected_type=type_hints["copyright_owner"])
            check_type(argname="argument copyright_period", value=copyright_period, expected_type=type_hints["copyright_period"])
            check_type(argname="argument dependabot", value=dependabot, expected_type=type_hints["dependabot"])
            check_type(argname="argument dependabot_options", value=dependabot_options, expected_type=type_hints["dependabot_options"])
            check_type(argname="argument deps_upgrade", value=deps_upgrade, expected_type=type_hints["deps_upgrade"])
            check_type(argname="argument deps_upgrade_options", value=deps_upgrade_options, expected_type=type_hints["deps_upgrade_options"])
            check_type(argname="argument gitignore", value=gitignore, expected_type=type_hints["gitignore"])
            check_type(argname="argument jest", value=jest, expected_type=type_hints["jest"])
            check_type(argname="argument jest_options", value=jest_options, expected_type=type_hints["jest_options"])
            check_type(argname="argument mutable_build", value=mutable_build, expected_type=type_hints["mutable_build"])
            check_type(argname="argument npmignore", value=npmignore, expected_type=type_hints["npmignore"])
            check_type(argname="argument npmignore_enabled", value=npmignore_enabled, expected_type=type_hints["npmignore_enabled"])
            check_type(argname="argument npm_ignore_options", value=npm_ignore_options, expected_type=type_hints["npm_ignore_options"])
            check_type(argname="argument package", value=package, expected_type=type_hints["package"])
            check_type(argname="argument prettier", value=prettier, expected_type=type_hints["prettier"])
            check_type(argname="argument prettier_options", value=prettier_options, expected_type=type_hints["prettier_options"])
            check_type(argname="argument projen_dev_dependency", value=projen_dev_dependency, expected_type=type_hints["projen_dev_dependency"])
            check_type(argname="argument projenrc_js", value=projenrc_js, expected_type=type_hints["projenrc_js"])
            check_type(argname="argument projenrc_js_options", value=projenrc_js_options, expected_type=type_hints["projenrc_js_options"])
            check_type(argname="argument projen_version", value=projen_version, expected_type=type_hints["projen_version"])
            check_type(argname="argument pull_request_template", value=pull_request_template, expected_type=type_hints["pull_request_template"])
            check_type(argname="argument pull_request_template_contents", value=pull_request_template_contents, expected_type=type_hints["pull_request_template_contents"])
            check_type(argname="argument release", value=release, expected_type=type_hints["release"])
            check_type(argname="argument release_to_npm", value=release_to_npm, expected_type=type_hints["release_to_npm"])
            check_type(argname="argument release_workflow", value=release_workflow, expected_type=type_hints["release_workflow"])
            check_type(argname="argument workflow_bootstrap_steps", value=workflow_bootstrap_steps, expected_type=type_hints["workflow_bootstrap_steps"])
            check_type(argname="argument workflow_git_identity", value=workflow_git_identity, expected_type=type_hints["workflow_git_identity"])
            check_type(argname="argument workflow_node_version", value=workflow_node_version, expected_type=type_hints["workflow_node_version"])
            check_type(argname="argument workflow_package_cache", value=workflow_package_cache, expected_type=type_hints["workflow_package_cache"])
            check_type(argname="argument disable_tsconfig", value=disable_tsconfig, expected_type=type_hints["disable_tsconfig"])
            check_type(argname="argument disable_tsconfig_dev", value=disable_tsconfig_dev, expected_type=type_hints["disable_tsconfig_dev"])
            check_type(argname="argument docgen", value=docgen, expected_type=type_hints["docgen"])
            check_type(argname="argument docs_directory", value=docs_directory, expected_type=type_hints["docs_directory"])
            check_type(argname="argument entrypoint_types", value=entrypoint_types, expected_type=type_hints["entrypoint_types"])
            check_type(argname="argument eslint", value=eslint, expected_type=type_hints["eslint"])
            check_type(argname="argument eslint_options", value=eslint_options, expected_type=type_hints["eslint_options"])
            check_type(argname="argument libdir", value=libdir, expected_type=type_hints["libdir"])
            check_type(argname="argument projenrc_ts", value=projenrc_ts, expected_type=type_hints["projenrc_ts"])
            check_type(argname="argument projenrc_ts_options", value=projenrc_ts_options, expected_type=type_hints["projenrc_ts_options"])
            check_type(argname="argument sample_code", value=sample_code, expected_type=type_hints["sample_code"])
            check_type(argname="argument srcdir", value=srcdir, expected_type=type_hints["srcdir"])
            check_type(argname="argument testdir", value=testdir, expected_type=type_hints["testdir"])
            check_type(argname="argument tsconfig", value=tsconfig, expected_type=type_hints["tsconfig"])
            check_type(argname="argument tsconfig_dev", value=tsconfig_dev, expected_type=type_hints["tsconfig_dev"])
            check_type(argname="argument tsconfig_dev_file", value=tsconfig_dev_file, expected_type=type_hints["tsconfig_dev_file"])
            check_type(argname="argument ts_jest_options", value=ts_jest_options, expected_type=type_hints["ts_jest_options"])
            check_type(argname="argument typescript_version", value=typescript_version, expected_type=type_hints["typescript_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "default_release_branch": default_release_branch,
        }
        if commit_generated is not None:
            self._values["commit_generated"] = commit_generated
        if git_ignore_options is not None:
            self._values["git_ignore_options"] = git_ignore_options
        if git_options is not None:
            self._values["git_options"] = git_options
        if logging is not None:
            self._values["logging"] = logging
        if outdir is not None:
            self._values["outdir"] = outdir
        if parent is not None:
            self._values["parent"] = parent
        if projen_command is not None:
            self._values["projen_command"] = projen_command
        if projenrc_json is not None:
            self._values["projenrc_json"] = projenrc_json
        if projenrc_json_options is not None:
            self._values["projenrc_json_options"] = projenrc_json_options
        if renovatebot is not None:
            self._values["renovatebot"] = renovatebot
        if renovatebot_options is not None:
            self._values["renovatebot_options"] = renovatebot_options
        if auto_approve_options is not None:
            self._values["auto_approve_options"] = auto_approve_options
        if auto_merge is not None:
            self._values["auto_merge"] = auto_merge
        if auto_merge_options is not None:
            self._values["auto_merge_options"] = auto_merge_options
        if clobber is not None:
            self._values["clobber"] = clobber
        if dev_container is not None:
            self._values["dev_container"] = dev_container
        if github is not None:
            self._values["github"] = github
        if github_options is not None:
            self._values["github_options"] = github_options
        if gitpod is not None:
            self._values["gitpod"] = gitpod
        if mergify is not None:
            self._values["mergify"] = mergify
        if mergify_options is not None:
            self._values["mergify_options"] = mergify_options
        if project_type is not None:
            self._values["project_type"] = project_type
        if projen_credentials is not None:
            self._values["projen_credentials"] = projen_credentials
        if projen_token_secret is not None:
            self._values["projen_token_secret"] = projen_token_secret
        if readme is not None:
            self._values["readme"] = readme
        if stale is not None:
            self._values["stale"] = stale
        if stale_options is not None:
            self._values["stale_options"] = stale_options
        if vscode is not None:
            self._values["vscode"] = vscode
        if allow_library_dependencies is not None:
            self._values["allow_library_dependencies"] = allow_library_dependencies
        if author_email is not None:
            self._values["author_email"] = author_email
        if author_name is not None:
            self._values["author_name"] = author_name
        if author_organization is not None:
            self._values["author_organization"] = author_organization
        if author_url is not None:
            self._values["author_url"] = author_url
        if auto_detect_bin is not None:
            self._values["auto_detect_bin"] = auto_detect_bin
        if bin is not None:
            self._values["bin"] = bin
        if bugs_email is not None:
            self._values["bugs_email"] = bugs_email
        if bugs_url is not None:
            self._values["bugs_url"] = bugs_url
        if bundled_deps is not None:
            self._values["bundled_deps"] = bundled_deps
        if bun_version is not None:
            self._values["bun_version"] = bun_version
        if code_artifact_options is not None:
            self._values["code_artifact_options"] = code_artifact_options
        if deps is not None:
            self._values["deps"] = deps
        if description is not None:
            self._values["description"] = description
        if dev_deps is not None:
            self._values["dev_deps"] = dev_deps
        if entrypoint is not None:
            self._values["entrypoint"] = entrypoint
        if homepage is not None:
            self._values["homepage"] = homepage
        if keywords is not None:
            self._values["keywords"] = keywords
        if license is not None:
            self._values["license"] = license
        if licensed is not None:
            self._values["licensed"] = licensed
        if max_node_version is not None:
            self._values["max_node_version"] = max_node_version
        if min_node_version is not None:
            self._values["min_node_version"] = min_node_version
        if npm_access is not None:
            self._values["npm_access"] = npm_access
        if npm_provenance is not None:
            self._values["npm_provenance"] = npm_provenance
        if npm_registry is not None:
            self._values["npm_registry"] = npm_registry
        if npm_registry_url is not None:
            self._values["npm_registry_url"] = npm_registry_url
        if npm_token_secret is not None:
            self._values["npm_token_secret"] = npm_token_secret
        if npm_trusted_publishing is not None:
            self._values["npm_trusted_publishing"] = npm_trusted_publishing
        if package_manager is not None:
            self._values["package_manager"] = package_manager
        if package_name is not None:
            self._values["package_name"] = package_name
        if peer_dependency_options is not None:
            self._values["peer_dependency_options"] = peer_dependency_options
        if peer_deps is not None:
            self._values["peer_deps"] = peer_deps
        if pnpm_version is not None:
            self._values["pnpm_version"] = pnpm_version
        if repository is not None:
            self._values["repository"] = repository
        if repository_directory is not None:
            self._values["repository_directory"] = repository_directory
        if scoped_packages_options is not None:
            self._values["scoped_packages_options"] = scoped_packages_options
        if scripts is not None:
            self._values["scripts"] = scripts
        if stability is not None:
            self._values["stability"] = stability
        if yarn_berry_options is not None:
            self._values["yarn_berry_options"] = yarn_berry_options
        if bump_package is not None:
            self._values["bump_package"] = bump_package
        if jsii_release_version is not None:
            self._values["jsii_release_version"] = jsii_release_version
        if major_version is not None:
            self._values["major_version"] = major_version
        if min_major_version is not None:
            self._values["min_major_version"] = min_major_version
        if next_version_command is not None:
            self._values["next_version_command"] = next_version_command
        if npm_dist_tag is not None:
            self._values["npm_dist_tag"] = npm_dist_tag
        if post_build_steps is not None:
            self._values["post_build_steps"] = post_build_steps
        if prerelease is not None:
            self._values["prerelease"] = prerelease
        if publish_dry_run is not None:
            self._values["publish_dry_run"] = publish_dry_run
        if publish_tasks is not None:
            self._values["publish_tasks"] = publish_tasks
        if releasable_commits is not None:
            self._values["releasable_commits"] = releasable_commits
        if release_branches is not None:
            self._values["release_branches"] = release_branches
        if release_environment is not None:
            self._values["release_environment"] = release_environment
        if release_every_commit is not None:
            self._values["release_every_commit"] = release_every_commit
        if release_failure_issue is not None:
            self._values["release_failure_issue"] = release_failure_issue
        if release_failure_issue_label is not None:
            self._values["release_failure_issue_label"] = release_failure_issue_label
        if release_schedule is not None:
            self._values["release_schedule"] = release_schedule
        if release_tag_prefix is not None:
            self._values["release_tag_prefix"] = release_tag_prefix
        if release_trigger is not None:
            self._values["release_trigger"] = release_trigger
        if release_workflow_env is not None:
            self._values["release_workflow_env"] = release_workflow_env
        if release_workflow_name is not None:
            self._values["release_workflow_name"] = release_workflow_name
        if release_workflow_setup_steps is not None:
            self._values["release_workflow_setup_steps"] = release_workflow_setup_steps
        if versionrc_options is not None:
            self._values["versionrc_options"] = versionrc_options
        if workflow_container_image is not None:
            self._values["workflow_container_image"] = workflow_container_image
        if workflow_runs_on is not None:
            self._values["workflow_runs_on"] = workflow_runs_on
        if workflow_runs_on_group is not None:
            self._values["workflow_runs_on_group"] = workflow_runs_on_group
        if artifacts_directory is not None:
            self._values["artifacts_directory"] = artifacts_directory
        if auto_approve_upgrades is not None:
            self._values["auto_approve_upgrades"] = auto_approve_upgrades
        if biome is not None:
            self._values["biome"] = biome
        if biome_options is not None:
            self._values["biome_options"] = biome_options
        if build_workflow is not None:
            self._values["build_workflow"] = build_workflow
        if build_workflow_options is not None:
            self._values["build_workflow_options"] = build_workflow_options
        if build_workflow_triggers is not None:
            self._values["build_workflow_triggers"] = build_workflow_triggers
        if bundler_options is not None:
            self._values["bundler_options"] = bundler_options
        if check_licenses is not None:
            self._values["check_licenses"] = check_licenses
        if code_cov is not None:
            self._values["code_cov"] = code_cov
        if code_cov_token_secret is not None:
            self._values["code_cov_token_secret"] = code_cov_token_secret
        if copyright_owner is not None:
            self._values["copyright_owner"] = copyright_owner
        if copyright_period is not None:
            self._values["copyright_period"] = copyright_period
        if dependabot is not None:
            self._values["dependabot"] = dependabot
        if dependabot_options is not None:
            self._values["dependabot_options"] = dependabot_options
        if deps_upgrade is not None:
            self._values["deps_upgrade"] = deps_upgrade
        if deps_upgrade_options is not None:
            self._values["deps_upgrade_options"] = deps_upgrade_options
        if gitignore is not None:
            self._values["gitignore"] = gitignore
        if jest is not None:
            self._values["jest"] = jest
        if jest_options is not None:
            self._values["jest_options"] = jest_options
        if mutable_build is not None:
            self._values["mutable_build"] = mutable_build
        if npmignore is not None:
            self._values["npmignore"] = npmignore
        if npmignore_enabled is not None:
            self._values["npmignore_enabled"] = npmignore_enabled
        if npm_ignore_options is not None:
            self._values["npm_ignore_options"] = npm_ignore_options
        if package is not None:
            self._values["package"] = package
        if prettier is not None:
            self._values["prettier"] = prettier
        if prettier_options is not None:
            self._values["prettier_options"] = prettier_options
        if projen_dev_dependency is not None:
            self._values["projen_dev_dependency"] = projen_dev_dependency
        if projenrc_js is not None:
            self._values["projenrc_js"] = projenrc_js
        if projenrc_js_options is not None:
            self._values["projenrc_js_options"] = projenrc_js_options
        if projen_version is not None:
            self._values["projen_version"] = projen_version
        if pull_request_template is not None:
            self._values["pull_request_template"] = pull_request_template
        if pull_request_template_contents is not None:
            self._values["pull_request_template_contents"] = pull_request_template_contents
        if release is not None:
            self._values["release"] = release
        if release_to_npm is not None:
            self._values["release_to_npm"] = release_to_npm
        if release_workflow is not None:
            self._values["release_workflow"] = release_workflow
        if workflow_bootstrap_steps is not None:
            self._values["workflow_bootstrap_steps"] = workflow_bootstrap_steps
        if workflow_git_identity is not None:
            self._values["workflow_git_identity"] = workflow_git_identity
        if workflow_node_version is not None:
            self._values["workflow_node_version"] = workflow_node_version
        if workflow_package_cache is not None:
            self._values["workflow_package_cache"] = workflow_package_cache
        if disable_tsconfig is not None:
            self._values["disable_tsconfig"] = disable_tsconfig
        if disable_tsconfig_dev is not None:
            self._values["disable_tsconfig_dev"] = disable_tsconfig_dev
        if docgen is not None:
            self._values["docgen"] = docgen
        if docs_directory is not None:
            self._values["docs_directory"] = docs_directory
        if entrypoint_types is not None:
            self._values["entrypoint_types"] = entrypoint_types
        if eslint is not None:
            self._values["eslint"] = eslint
        if eslint_options is not None:
            self._values["eslint_options"] = eslint_options
        if libdir is not None:
            self._values["libdir"] = libdir
        if projenrc_ts is not None:
            self._values["projenrc_ts"] = projenrc_ts
        if projenrc_ts_options is not None:
            self._values["projenrc_ts_options"] = projenrc_ts_options
        if sample_code is not None:
            self._values["sample_code"] = sample_code
        if srcdir is not None:
            self._values["srcdir"] = srcdir
        if testdir is not None:
            self._values["testdir"] = testdir
        if tsconfig is not None:
            self._values["tsconfig"] = tsconfig
        if tsconfig_dev is not None:
            self._values["tsconfig_dev"] = tsconfig_dev
        if tsconfig_dev_file is not None:
            self._values["tsconfig_dev_file"] = tsconfig_dev_file
        if ts_jest_options is not None:
            self._values["ts_jest_options"] = ts_jest_options
        if typescript_version is not None:
            self._values["typescript_version"] = typescript_version

    @builtins.property
    def name(self) -> builtins.str:
        '''(experimental) This is the name of your project.

        :default: $BASEDIR

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def commit_generated(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Whether to commit the managed files by default.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("commit_generated")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def git_ignore_options(self) -> typing.Optional[_IgnoreFileOptions_86c48b91]:
        '''(experimental) Configuration options for .gitignore file.

        :stability: experimental
        '''
        result = self._values.get("git_ignore_options")
        return typing.cast(typing.Optional[_IgnoreFileOptions_86c48b91], result)

    @builtins.property
    def git_options(self) -> typing.Optional[_GitOptions_a65916a3]:
        '''(experimental) Configuration options for git.

        :stability: experimental
        '''
        result = self._values.get("git_options")
        return typing.cast(typing.Optional[_GitOptions_a65916a3], result)

    @builtins.property
    def logging(self) -> typing.Optional[_LoggerOptions_eb0f6309]:
        '''(experimental) Configure logging options such as verbosity.

        :default: {}

        :stability: experimental
        '''
        result = self._values.get("logging")
        return typing.cast(typing.Optional[_LoggerOptions_eb0f6309], result)

    @builtins.property
    def outdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) The root directory of the project.

        Relative to this directory, all files are synthesized.

        If this project has a parent, this directory is relative to the parent
        directory and it cannot be the same as the parent or any of it's other
        subprojects.

        :default: "."

        :stability: experimental
        '''
        result = self._values.get("outdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent(self) -> typing.Optional[_Project_57d89203]:
        '''(experimental) The parent project, if this project is part of a bigger project.

        :stability: experimental
        '''
        result = self._values.get("parent")
        return typing.cast(typing.Optional[_Project_57d89203], result)

    @builtins.property
    def projen_command(self) -> typing.Optional[builtins.str]:
        '''(experimental) The shell command to use in order to run the projen CLI.

        Can be used to customize in special environments.

        :default: "npx projen"

        :stability: experimental
        '''
        result = self._values.get("projen_command")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projenrc_json(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("projenrc_json")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_json_options(self) -> typing.Optional[_ProjenrcJsonOptions_9c40dd4f]:
        '''(experimental) Options for .projenrc.json.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("projenrc_json_options")
        return typing.cast(typing.Optional[_ProjenrcJsonOptions_9c40dd4f], result)

    @builtins.property
    def renovatebot(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use renovatebot to handle dependency upgrades.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("renovatebot")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def renovatebot_options(self) -> typing.Optional[_RenovatebotOptions_18e6b8a1]:
        '''(experimental) Options for renovatebot.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("renovatebot_options")
        return typing.cast(typing.Optional[_RenovatebotOptions_18e6b8a1], result)

    @builtins.property
    def auto_approve_options(self) -> typing.Optional[_AutoApproveOptions_dac86cbe]:
        '''(experimental) Enable and configure the 'auto approve' workflow.

        :default: - auto approve is disabled

        :stability: experimental
        '''
        result = self._values.get("auto_approve_options")
        return typing.cast(typing.Optional[_AutoApproveOptions_dac86cbe], result)

    @builtins.property
    def auto_merge(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable automatic merging on GitHub.

        Has no effect if ``github.mergify``
        is set to false.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("auto_merge")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def auto_merge_options(self) -> typing.Optional[_AutoMergeOptions_d112cd3c]:
        '''(experimental) Configure options for automatic merging on GitHub.

        Has no effect if
        ``github.mergify`` or ``autoMerge`` is set to false.

        :default: - see defaults in ``AutoMergeOptions``

        :stability: experimental
        '''
        result = self._values.get("auto_merge_options")
        return typing.cast(typing.Optional[_AutoMergeOptions_d112cd3c], result)

    @builtins.property
    def clobber(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a ``clobber`` task which resets the repo to origin.

        :default: - true, but false for subprojects

        :stability: experimental
        '''
        result = self._values.get("clobber")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dev_container(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a VSCode development environment (used for GitHub Codespaces).

        :default: false

        :stability: experimental
        '''
        result = self._values.get("dev_container")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def github(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable GitHub integration.

        Enabled by default for root projects. Disabled for non-root projects.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("github")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def github_options(self) -> typing.Optional[_GitHubOptions_21553699]:
        '''(experimental) Options for GitHub integration.

        :default: - see GitHubOptions

        :stability: experimental
        '''
        result = self._values.get("github_options")
        return typing.cast(typing.Optional[_GitHubOptions_21553699], result)

    @builtins.property
    def gitpod(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a Gitpod development environment.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("gitpod")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def mergify(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Whether mergify should be enabled on this repository or not.

        :default: true

        :deprecated: use ``githubOptions.mergify`` instead

        :stability: deprecated
        '''
        result = self._values.get("mergify")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def mergify_options(self) -> typing.Optional[_MergifyOptions_a6faaab3]:
        '''(deprecated) Options for mergify.

        :default: - default options

        :deprecated: use ``githubOptions.mergifyOptions`` instead

        :stability: deprecated
        '''
        result = self._values.get("mergify_options")
        return typing.cast(typing.Optional[_MergifyOptions_a6faaab3], result)

    @builtins.property
    def project_type(self) -> typing.Optional[_ProjectType_fd80c725]:
        '''(deprecated) Which type of project this is (library/app).

        :default: ProjectType.UNKNOWN

        :deprecated: no longer supported at the base project level

        :stability: deprecated
        '''
        result = self._values.get("project_type")
        return typing.cast(typing.Optional[_ProjectType_fd80c725], result)

    @builtins.property
    def projen_credentials(self) -> typing.Optional[_GithubCredentials_ae257072]:
        '''(experimental) Choose a method of providing GitHub API access for projen workflows.

        :default: - use a personal access token named PROJEN_GITHUB_TOKEN

        :stability: experimental
        '''
        result = self._values.get("projen_credentials")
        return typing.cast(typing.Optional[_GithubCredentials_ae257072], result)

    @builtins.property
    def projen_token_secret(self) -> typing.Optional[builtins.str]:
        '''(deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows.

        This token needs to have the ``repo``, ``workflows``
        and ``packages`` scope.

        :default: "PROJEN_GITHUB_TOKEN"

        :deprecated: use ``projenCredentials``

        :stability: deprecated
        '''
        result = self._values.get("projen_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def readme(self) -> typing.Optional[_SampleReadmeProps_3518b03b]:
        '''(experimental) The README setup.

        :default: - { filename: 'README.md', contents: '# replace this' }

        :stability: experimental

        Example::

            "{ filename: 'readme.md', contents: '# title' }"
        '''
        result = self._values.get("readme")
        return typing.cast(typing.Optional[_SampleReadmeProps_3518b03b], result)

    @builtins.property
    def stale(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Auto-close of stale issues and pull request.

        See ``staleOptions`` for options.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("stale")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def stale_options(self) -> typing.Optional[_StaleOptions_929db764]:
        '''(experimental) Auto-close stale issues and pull requests.

        To disable set ``stale`` to ``false``.

        :default: - see defaults in ``StaleOptions``

        :stability: experimental
        '''
        result = self._values.get("stale_options")
        return typing.cast(typing.Optional[_StaleOptions_929db764], result)

    @builtins.property
    def vscode(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable VSCode integration.

        Enabled by default for root projects. Disabled for non-root projects.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("vscode")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_library_dependencies(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``.

        This is normally only allowed for libraries. For apps, there's no meaning
        for specifying these.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("allow_library_dependencies")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def author_email(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's e-mail.

        :stability: experimental
        '''
        result = self._values.get("author_email")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def author_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's name.

        :stability: experimental
        '''
        result = self._values.get("author_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def author_organization(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Is the author an organization.

        :stability: experimental
        '''
        result = self._values.get("author_organization")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def author_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's URL / Website.

        :stability: experimental
        '''
        result = self._values.get("author_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auto_detect_bin(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("auto_detect_bin")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def bin(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Binary programs vended with your module.

        You can use this option to add/customize how binaries are represented in
        your ``package.json``, but unless ``autoDetectBin`` is ``false``, every
        executable file under ``bin`` will automatically be added to this section.

        :stability: experimental
        '''
        result = self._values.get("bin")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def bugs_email(self) -> typing.Optional[builtins.str]:
        '''(experimental) The email address to which issues should be reported.

        :stability: experimental
        '''
        result = self._values.get("bugs_email")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bugs_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) The url to your project's issue tracker.

        :stability: experimental
        '''
        result = self._values.get("bugs_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bundled_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) List of dependencies to bundle into this module.

        These modules will be
        added both to the ``dependencies`` section and ``bundledDependencies`` section of
        your ``package.json``.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :stability: experimental
        '''
        result = self._values.get("bundled_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def bun_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of Bun to use if using Bun as a package manager.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("bun_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def code_artifact_options(self) -> typing.Optional[_CodeArtifactOptions_e4782b3e]:
        '''(experimental) Options for npm packages using AWS CodeArtifact.

        This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact

        :default: - undefined

        :stability: experimental
        '''
        result = self._values.get("code_artifact_options")
        return typing.cast(typing.Optional[_CodeArtifactOptions_e4782b3e], result)

    @builtins.property
    def deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Runtime dependencies of this module.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :default: []

        :stability: experimental
        :featured: true

        Example::

            [ 'express', 'lodash', 'foo@^2' ]
        '''
        result = self._values.get("deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description is just a string that helps people understand the purpose of the package.

        It can be used when searching for packages in a package manager as well.
        See https://classic.yarnpkg.com/en/docs/package-json/#toc-description

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dev_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Build dependencies for this module.

        These dependencies will only be
        available in your build environment but will not be fetched when this
        module is consumed.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :default: []

        :stability: experimental
        :featured: true

        Example::

            [ 'typescript', '@types/express' ]
        '''
        result = self._values.get("dev_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def entrypoint(self) -> typing.Optional[builtins.str]:
        '''(experimental) Module entrypoint (``main`` in ``package.json``).

        Set to an empty string to not include ``main`` in your package.json

        :default: "lib/index.js"

        :stability: experimental
        '''
        result = self._values.get("entrypoint")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def homepage(self) -> typing.Optional[builtins.str]:
        '''(experimental) Package's Homepage / Website.

        :stability: experimental
        '''
        result = self._values.get("homepage")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def keywords(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Keywords to include in ``package.json``.

        :stability: experimental
        '''
        result = self._values.get("keywords")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def license(self) -> typing.Optional[builtins.str]:
        '''(experimental) License's SPDX identifier.

        See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses.
        Use the ``licensed`` option if you want to no license to be specified.

        :default: "Apache-2.0"

        :stability: experimental
        '''
        result = self._values.get("license")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def licensed(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Indicates if a license should be added.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("licensed")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def max_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The maximum node version supported by this package. Most projects should not use this option.

        The value indicates that the package is incompatible with any newer versions of node.
        This requirement is enforced via the engines field.

        You will normally not need to set this option.
        Consider this option only if your package is known to not function with newer versions of node.

        :default: - no maximum version is enforced

        :stability: experimental
        '''
        result = self._values.get("max_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def min_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The minimum node version required by this package to function. Most projects should not use this option.

        The value indicates that the package is incompatible with any older versions of node.
        This requirement is enforced via the engines field.

        You will normally not need to set this option, even if your package is incompatible with EOL versions of node.
        Consider this option only if your package depends on a specific feature, that is not available in other LTS versions.
        Setting this option has very high impact on the consumers of your package,
        as package managers will actively prevent usage with node versions you have marked as incompatible.

        To change the node version of your CI/CD workflows, use ``workflowNodeVersion``.

        :default: - no minimum version is enforced

        :stability: experimental
        '''
        result = self._values.get("min_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_access(self) -> typing.Optional[_NpmAccess_134fa228]:
        '''(experimental) Access level of the npm package.

        :default:

        - for scoped packages (e.g. ``foo@bar``), the default is
        ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is
        ``NpmAccess.PUBLIC``.

        :stability: experimental
        '''
        result = self._values.get("npm_access")
        return typing.cast(typing.Optional[_NpmAccess_134fa228], result)

    @builtins.property
    def npm_provenance(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Should provenance statements be generated when the package is published.

        A supported package manager is required to publish a package with npm provenance statements and
        you will need to use a supported CI/CD provider.

        Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages,
        which is using npm internally and supports provenance statements independently of the package manager used.

        :default: - true for public packages, false otherwise

        :see: https://docs.npmjs.com/generating-provenance-statements
        :stability: experimental
        '''
        result = self._values.get("npm_provenance")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npm_registry(self) -> typing.Optional[builtins.str]:
        '''(deprecated) The host name of the npm registry to publish to.

        Cannot be set together with ``npmRegistryUrl``.

        :deprecated: use ``npmRegistryUrl`` instead

        :stability: deprecated
        '''
        result = self._values.get("npm_registry")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_registry_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) The base URL of the npm package registry.

        Must be a URL (e.g. start with "https://" or "http://")

        :default: "https://registry.npmjs.org"

        :stability: experimental
        '''
        result = self._values.get("npm_registry_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_token_secret(self) -> typing.Optional[builtins.str]:
        '''(experimental) GitHub secret which contains the NPM token to use when publishing packages.

        :default: "NPM_TOKEN"

        :stability: experimental
        '''
        result = self._values.get("npm_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_trusted_publishing(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work.

        :default: - false

        :stability: experimental
        '''
        result = self._values.get("npm_trusted_publishing")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def package_manager(self) -> typing.Optional[_NodePackageManager_3eb53bf6]:
        '''(experimental) The Node Package Manager used to execute scripts.

        :default: NodePackageManager.YARN_CLASSIC

        :stability: experimental
        '''
        result = self._values.get("package_manager")
        return typing.cast(typing.Optional[_NodePackageManager_3eb53bf6], result)

    @builtins.property
    def package_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The "name" in package.json.

        :default: - defaults to project name

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("package_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def peer_dependency_options(
        self,
    ) -> typing.Optional[_PeerDependencyOptions_99d7d493]:
        '''(experimental) Options for ``peerDeps``.

        :stability: experimental
        '''
        result = self._values.get("peer_dependency_options")
        return typing.cast(typing.Optional[_PeerDependencyOptions_99d7d493], result)

    @builtins.property
    def peer_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Peer dependencies for this module.

        Dependencies listed here are required to
        be installed (and satisfied) by the *consumer* of this library. Using peer
        dependencies allows you to ensure that only a single module of a certain
        library exists in the ``node_modules`` tree of your consumers.

        Note that prior to npm@7, peer dependencies are *not* automatically
        installed, which means that adding peer dependencies to a library will be a
        breaking change for your customers.

        Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is
        enabled by default), projen will automatically add a dev dependency with a
        pinned version for each peer dependency. This will ensure that you build &
        test your module against the lowest peer version required.

        :default: []

        :stability: experimental
        '''
        result = self._values.get("peer_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def pnpm_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of PNPM to use if using PNPM as a package manager.

        :default: "9"

        :stability: experimental
        '''
        result = self._values.get("pnpm_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repository(self) -> typing.Optional[builtins.str]:
        '''(experimental) The repository is the location where the actual code for your package lives.

        See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository

        :stability: experimental
        '''
        result = self._values.get("repository")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repository_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.

        :stability: experimental
        '''
        result = self._values.get("repository_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scoped_packages_options(
        self,
    ) -> typing.Optional[typing.List[_ScopedPackagesOptions_52f0a477]]:
        '''(experimental) Options for privately hosted scoped packages.

        :default: - fetch all scoped packages from the public npm registry

        :stability: experimental
        '''
        result = self._values.get("scoped_packages_options")
        return typing.cast(typing.Optional[typing.List[_ScopedPackagesOptions_52f0a477]], result)

    @builtins.property
    def scripts(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(deprecated) npm scripts to include.

        If a script has the same name as a standard script,
        the standard script will be overwritten.
        Also adds the script as a task.

        :default: {}

        :deprecated: use ``project.addTask()`` or ``package.setScript()``

        :stability: deprecated
        '''
        result = self._values.get("scripts")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def stability(self) -> typing.Optional[builtins.str]:
        '''(experimental) Package's Stability.

        :stability: experimental
        '''
        result = self._values.get("stability")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def yarn_berry_options(self) -> typing.Optional[_YarnBerryOptions_b6942539]:
        '''(experimental) Options for Yarn Berry.

        :default: - Yarn Berry v4 with all default options

        :stability: experimental
        '''
        result = self._values.get("yarn_berry_options")
        return typing.cast(typing.Optional[_YarnBerryOptions_b6942539], result)

    @builtins.property
    def bump_package(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string.

        This can be any compatible package version, including the deprecated ``standard-version@9``.

        :default: - A recent version of "commit-and-tag-version"

        :stability: experimental
        '''
        result = self._values.get("bump_package")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsii_release_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) Version requirement of ``publib`` which is used to publish modules to npm.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("jsii_release_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def major_version(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Major version to release from the default branch.

        If this is specified, we bump the latest version of this major version line.
        If not specified, we bump the global latest version.

        :default: - Major version is not enforced.

        :stability: experimental
        '''
        result = self._values.get("major_version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_major_version(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Minimal Major version to release.

        This can be useful to set to 1, as breaking changes before the 1.x major
        release are not incrementing the major version number.

        Can not be set together with ``majorVersion``.

        :default: - No minimum version is being enforced

        :stability: experimental
        '''
        result = self._values.get("min_major_version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def next_version_command(self) -> typing.Optional[builtins.str]:
        '''(experimental) A shell command to control the next version to release.

        If present, this shell command will be run before the bump is executed, and
        it determines what version to release. It will be executed in the following
        environment:

        - Working directory: the project directory.
        - ``$VERSION``: the current version. Looks like ``1.2.3``.
        - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset.
        - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``.

        The command should print one of the following to ``stdout``:

        - Nothing: the next version number will be determined based on commit history.
        - ``x.y.z``: the next version number will be ``x.y.z``.
        - ``major|minor|patch``: the next version number will be the current version number
          with the indicated component bumped.

        This setting cannot be specified together with ``minMajorVersion``; the invoked
        script can be used to achieve the effects of ``minMajorVersion``.

        :default: - The next version will be determined based on the commit history and project settings.

        :stability: experimental
        '''
        result = self._values.get("next_version_command")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_dist_tag(self) -> typing.Optional[builtins.str]:
        '''(experimental) The npmDistTag to use when publishing from the default branch.

        To set the npm dist-tag for release branches, set the ``npmDistTag`` property
        for each branch.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("npm_dist_tag")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def post_build_steps(self) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) Steps to execute after build as part of the release workflow.

        :default: []

        :stability: experimental
        '''
        result = self._values.get("post_build_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def prerelease(self) -> typing.Optional[builtins.str]:
        '''(experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre").

        :default: - normal semantic versions

        :stability: experimental
        '''
        result = self._values.get("prerelease")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def publish_dry_run(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Instead of actually publishing to package managers, just print the publishing command.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("publish_dry_run")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def publish_tasks(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define publishing tasks that can be executed manually as well as workflows.

        Normally, publishing only happens within automated workflows. Enable this
        in order to create a publishing task for each publishing activity.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("publish_tasks")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def releasable_commits(self) -> typing.Optional[_ReleasableCommits_d481ce10]:
        '''(experimental) Find commits that should be considered releasable Used to decide if a release is required.

        :default: ReleasableCommits.everyCommit()

        :stability: experimental
        '''
        result = self._values.get("releasable_commits")
        return typing.cast(typing.Optional[_ReleasableCommits_d481ce10], result)

    @builtins.property
    def release_branches(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, _BranchOptions_13663d08]]:
        '''(experimental) Defines additional release branches.

        A workflow will be created for each
        release branch which will publish releases from commits in this branch.
        Each release branch *must* be assigned a major version number which is used
        to enforce that versions published from that branch always use that major
        version. If multiple branches are used, the ``majorVersion`` field must also
        be provided for the default branch.

        :default:

        - no additional branches are used for release. you can use
        ``addBranch()`` to add additional branches.

        :stability: experimental
        '''
        result = self._values.get("release_branches")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, _BranchOptions_13663d08]], result)

    @builtins.property
    def release_environment(self) -> typing.Optional[builtins.str]:
        '''(experimental) The GitHub Actions environment used for the release.

        This can be used to add an explicit approval step to the release
        or limit who can initiate a release through environment protection rules.

        When multiple artifacts are released, the environment can be overwritten
        on a per artifact basis.

        :default: - no environment used, unless set at the artifact level

        :stability: experimental
        '''
        result = self._values.get("release_environment")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_every_commit(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``.

        :default: true

        :deprecated: Use ``releaseTrigger: ReleaseTrigger.continuous()`` instead

        :stability: deprecated
        '''
        result = self._values.get("release_every_commit")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_failure_issue(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Create a github issue on every failed publishing task.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("release_failure_issue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_failure_issue_label(self) -> typing.Optional[builtins.str]:
        '''(experimental) The label to apply to issues indicating publish failures.

        Only applies if ``releaseFailureIssue`` is true.

        :default: "failed-release"

        :stability: experimental
        '''
        result = self._values.get("release_failure_issue_label")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_schedule(self) -> typing.Optional[builtins.str]:
        '''(deprecated) CRON schedule to trigger new releases.

        :default: - no scheduled releases

        :deprecated: Use ``releaseTrigger: ReleaseTrigger.scheduled()`` instead

        :stability: deprecated
        '''
        result = self._values.get("release_schedule")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_tag_prefix(self) -> typing.Optional[builtins.str]:
        '''(experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers.

        Note: this prefix is used to detect the latest tagged version
        when bumping, so if you change this on a project with an existing version
        history, you may need to manually tag your latest release
        with the new prefix.

        :default: "v"

        :stability: experimental
        '''
        result = self._values.get("release_tag_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_trigger(self) -> typing.Optional[_ReleaseTrigger_e4dc221f]:
        '''(experimental) The release trigger to use.

        :default: - Continuous releases (``ReleaseTrigger.continuous()``)

        :stability: experimental
        '''
        result = self._values.get("release_trigger")
        return typing.cast(typing.Optional[_ReleaseTrigger_e4dc221f], result)

    @builtins.property
    def release_workflow_env(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Build environment variables for release workflows.

        :default: {}

        :stability: experimental
        '''
        result = self._values.get("release_workflow_env")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def release_workflow_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the default release workflow.

        :default: "release"

        :stability: experimental
        '''
        result = self._values.get("release_workflow_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_workflow_setup_steps(
        self,
    ) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) A set of workflow steps to execute in order to setup the workflow container.

        :stability: experimental
        '''
        result = self._values.get("release_workflow_setup_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def versionrc_options(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''(experimental) Custom configuration used when creating changelog with commit-and-tag-version package.

        Given values either append to default configuration or overwrite values in it.

        :default: - standard configuration applicable for GitHub repositories

        :stability: experimental
        '''
        result = self._values.get("versionrc_options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def workflow_container_image(self) -> typing.Optional[builtins.str]:
        '''(experimental) Container image to use for GitHub workflows.

        :default: - default image

        :stability: experimental
        '''
        result = self._values.get("workflow_container_image")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workflow_runs_on(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Github Runner selection labels.

        :default: ["ubuntu-latest"]

        :stability: experimental
        :description: Defines a target Runner by labels
        :throws: {Error} if both ``runsOn`` and ``runsOnGroup`` are specified
        '''
        result = self._values.get("workflow_runs_on")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def workflow_runs_on_group(self) -> typing.Optional[_GroupRunnerOptions_148c59c1]:
        '''(experimental) Github Runner Group selection options.

        :stability: experimental
        :description: Defines a target Runner Group by name and/or labels
        :throws: {Error} if both ``runsOn`` and ``runsOnGroup`` are specified
        '''
        result = self._values.get("workflow_runs_on_group")
        return typing.cast(typing.Optional[_GroupRunnerOptions_148c59c1], result)

    @builtins.property
    def default_release_branch(self) -> builtins.str:
        '''(experimental) The name of the main release branch.

        :default: "main"

        :stability: experimental
        '''
        result = self._values.get("default_release_branch")
        assert result is not None, "Required property 'default_release_branch' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def artifacts_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) A directory which will contain build artifacts.

        :default: "dist"

        :stability: experimental
        '''
        result = self._values.get("artifacts_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auto_approve_upgrades(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued).

        Throw if set to true but ``autoApproveOptions`` are not defined.

        :default: - true

        :stability: experimental
        '''
        result = self._values.get("auto_approve_upgrades")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def biome(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup Biome.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("biome")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def biome_options(self) -> typing.Optional[_BiomeOptions_452ab984]:
        '''(experimental) Biome options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("biome_options")
        return typing.cast(typing.Optional[_BiomeOptions_452ab984], result)

    @builtins.property
    def build_workflow(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define a GitHub workflow for building PRs.

        :default: - true if not a subproject

        :stability: experimental
        '''
        result = self._values.get("build_workflow")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def build_workflow_options(self) -> typing.Optional[_BuildWorkflowOptions_b756f97f]:
        '''(experimental) Options for PR build workflow.

        :stability: experimental
        '''
        result = self._values.get("build_workflow_options")
        return typing.cast(typing.Optional[_BuildWorkflowOptions_b756f97f], result)

    @builtins.property
    def build_workflow_triggers(self) -> typing.Optional[_Triggers_e9ae7617]:
        '''(deprecated) Build workflow triggers.

        :default: "{ pullRequest: {}, workflowDispatch: {} }"

        :deprecated: - Use ``buildWorkflowOptions.workflowTriggers``

        :stability: deprecated
        '''
        result = self._values.get("build_workflow_triggers")
        return typing.cast(typing.Optional[_Triggers_e9ae7617], result)

    @builtins.property
    def bundler_options(self) -> typing.Optional[_BundlerOptions_d60b85ed]:
        '''(experimental) Options for ``Bundler``.

        :stability: experimental
        '''
        result = self._values.get("bundler_options")
        return typing.cast(typing.Optional[_BundlerOptions_d60b85ed], result)

    @builtins.property
    def check_licenses(self) -> typing.Optional[_LicenseCheckerOptions_80bcd362]:
        '''(experimental) Configure which licenses should be deemed acceptable for use by dependencies.

        This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered.

        :default: - no license checks are run during the build and all licenses will be accepted

        :stability: experimental
        '''
        result = self._values.get("check_licenses")
        return typing.cast(typing.Optional[_LicenseCheckerOptions_80bcd362], result)

    @builtins.property
    def code_cov(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("code_cov")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def code_cov_token_secret(self) -> typing.Optional[builtins.str]:
        '''(experimental) Define the secret name for a specified https://codecov.io/ token.

        :default: - OIDC auth is used

        :stability: experimental
        '''
        result = self._values.get("code_cov_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def copyright_owner(self) -> typing.Optional[builtins.str]:
        '''(experimental) License copyright owner.

        :default: - defaults to the value of authorName or "" if ``authorName`` is undefined.

        :stability: experimental
        '''
        result = self._values.get("copyright_owner")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def copyright_period(self) -> typing.Optional[builtins.str]:
        '''(experimental) The copyright years to put in the LICENSE file.

        :default: - current year

        :stability: experimental
        '''
        result = self._values.get("copyright_period")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dependabot(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use dependabot to handle dependency upgrades.

        Cannot be used in conjunction with ``depsUpgrade``.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("dependabot")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dependabot_options(self) -> typing.Optional[_DependabotOptions_0cedc635]:
        '''(experimental) Options for dependabot.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("dependabot_options")
        return typing.cast(typing.Optional[_DependabotOptions_0cedc635], result)

    @builtins.property
    def deps_upgrade(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use tasks and github workflows to handle dependency upgrades.

        Cannot be used in conjunction with ``dependabot``.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("deps_upgrade")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deps_upgrade_options(
        self,
    ) -> typing.Optional[_UpgradeDependenciesOptions_1d8ce4da]:
        '''(experimental) Options for ``UpgradeDependencies``.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("deps_upgrade_options")
        return typing.cast(typing.Optional[_UpgradeDependenciesOptions_1d8ce4da], result)

    @builtins.property
    def gitignore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Additional entries to .gitignore.

        :stability: experimental
        '''
        result = self._values.get("gitignore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def jest(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup jest unit tests.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("jest")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def jest_options(self) -> typing.Optional[_JestOptions_a085f64e]:
        '''(experimental) Jest options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("jest_options")
        return typing.cast(typing.Optional[_JestOptions_a085f64e], result)

    @builtins.property
    def mutable_build(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Automatically update files modified during builds to pull-request branches.

        This means
        that any files synthesized by projen or e.g. test snapshots will always be up-to-date
        before a PR is merged.

        Implies that PR builds do not have anti-tamper checks.

        :default: true

        :deprecated: - Use ``buildWorkflowOptions.mutableBuild``

        :stability: deprecated
        '''
        result = self._values.get("mutable_build")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npmignore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(deprecated) Additional entries to .npmignore.

        :deprecated: - use ``project.addPackageIgnore``

        :stability: deprecated
        '''
        result = self._values.get("npmignore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def npmignore_enabled(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("npmignore_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npm_ignore_options(self) -> typing.Optional[_IgnoreFileOptions_86c48b91]:
        '''(experimental) Configuration options for .npmignore file.

        :stability: experimental
        '''
        result = self._values.get("npm_ignore_options")
        return typing.cast(typing.Optional[_IgnoreFileOptions_86c48b91], result)

    @builtins.property
    def package(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``).

        :default: true

        :stability: experimental
        '''
        result = self._values.get("package")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def prettier(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup prettier.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("prettier")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def prettier_options(self) -> typing.Optional[_PrettierOptions_41a5f203]:
        '''(experimental) Prettier options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("prettier_options")
        return typing.cast(typing.Optional[_PrettierOptions_41a5f203], result)

    @builtins.property
    def projen_dev_dependency(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Indicates of "projen" should be installed as a devDependency.

        :default: - true if not a subproject

        :stability: experimental
        '''
        result = self._values.get("projen_dev_dependency")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_js(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation.

        :default: - true if projenrcJson is false

        :stability: experimental
        '''
        result = self._values.get("projenrc_js")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_js_options(self) -> typing.Optional[_ProjenrcOptions_179dd39f]:
        '''(experimental) Options for .projenrc.js.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("projenrc_js_options")
        return typing.cast(typing.Optional[_ProjenrcOptions_179dd39f], result)

    @builtins.property
    def projen_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) Version of projen to install.

        :default: - Defaults to the latest version.

        :stability: experimental
        '''
        result = self._values.get("projen_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pull_request_template(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Include a GitHub pull request template.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("pull_request_template")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def pull_request_template_contents(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The contents of the pull request template.

        :default: - default content

        :stability: experimental
        '''
        result = self._values.get("pull_request_template_contents")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def release(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add release management to this project.

        :default: - true (false for subprojects)

        :stability: experimental
        '''
        result = self._values.get("release")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_to_npm(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically release to npm when new versions are introduced.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("release_to_npm")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_workflow(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) DEPRECATED: renamed to ``release``.

        :default: - true if not a subproject

        :deprecated: see ``release``.

        :stability: deprecated
        '''
        result = self._values.get("release_workflow")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def workflow_bootstrap_steps(
        self,
    ) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) Workflow steps to use in order to bootstrap this repo.

        :default: "yarn install --frozen-lockfile && yarn projen"

        :stability: experimental
        '''
        result = self._values.get("workflow_bootstrap_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def workflow_git_identity(self) -> typing.Optional[_GitIdentity_6effc3de]:
        '''(experimental) The git identity to use in workflows.

        :default: - default GitHub Actions user

        :stability: experimental
        '''
        result = self._values.get("workflow_git_identity")
        return typing.cast(typing.Optional[_GitIdentity_6effc3de], result)

    @builtins.property
    def workflow_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The node version used in GitHub Actions workflows.

        Always use this option if your GitHub Actions workflows require a specific to run.

        :default: - ``minNodeVersion`` if set, otherwise ``lts/*``.

        :stability: experimental
        '''
        result = self._values.get("workflow_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workflow_package_cache(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable Node.js package cache in GitHub workflows.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("workflow_package_cache")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disable_tsconfig(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler).

        :default: false

        :stability: experimental
        '''
        result = self._values.get("disable_tsconfig")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disable_tsconfig_dev(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Do not generate a ``tsconfig.dev.json`` file.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("disable_tsconfig_dev")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def docgen(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Docgen by Typedoc.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("docgen")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def docs_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) Docs directory.

        :default: "docs"

        :stability: experimental
        '''
        result = self._values.get("docs_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def entrypoint_types(self) -> typing.Optional[builtins.str]:
        '''(experimental) The .d.ts file that includes the type declarations for this module.

        :default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)

        :stability: experimental
        '''
        result = self._values.get("entrypoint_types")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def eslint(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup eslint.

        :default: - true, unless biome is enabled

        :stability: experimental
        '''
        result = self._values.get("eslint")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def eslint_options(self) -> typing.Optional[_EslintOptions_824f60bb]:
        '''(experimental) Eslint options.

        :default: - opinionated default options

        :stability: experimental
        '''
        result = self._values.get("eslint_options")
        return typing.cast(typing.Optional[_EslintOptions_824f60bb], result)

    @builtins.property
    def libdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Typescript  artifacts output directory.

        :default: "lib"

        :stability: experimental
        '''
        result = self._values.get("libdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projenrc_ts(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use TypeScript for your projenrc file (``.projenrc.ts``).

        :default: false

        :stability: experimental
        :pjnew: true
        '''
        result = self._values.get("projenrc_ts")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_ts_options(self) -> typing.Optional[ProjenrcOptions]:
        '''(experimental) Options for .projenrc.ts.

        :stability: experimental
        '''
        result = self._values.get("projenrc_ts_options")
        return typing.cast(typing.Optional[ProjenrcOptions], result)

    @builtins.property
    def sample_code(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("sample_code")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def srcdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Typescript sources directory.

        :default: "src"

        :stability: experimental
        '''
        result = self._values.get("srcdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def testdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``.

        If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``),
        then tests are going to be compiled into ``lib/`` and executed as javascript.
        If the test directory is outside of ``src``, then we configure jest to
        compile the code in-memory.

        :default: "test"

        :stability: experimental
        '''
        result = self._values.get("testdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tsconfig(self) -> typing.Optional[_TypescriptConfigOptions_8c5492cd]:
        '''(experimental) Custom TSConfig.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("tsconfig")
        return typing.cast(typing.Optional[_TypescriptConfigOptions_8c5492cd], result)

    @builtins.property
    def tsconfig_dev(self) -> typing.Optional[_TypescriptConfigOptions_8c5492cd]:
        '''(experimental) Custom tsconfig options for the development tsconfig.json file (used for testing).

        :default: - use the production tsconfig options

        :stability: experimental
        '''
        result = self._values.get("tsconfig_dev")
        return typing.cast(typing.Optional[_TypescriptConfigOptions_8c5492cd], result)

    @builtins.property
    def tsconfig_dev_file(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the development tsconfig.json file.

        :default: "tsconfig.dev.json"

        :stability: experimental
        '''
        result = self._values.get("tsconfig_dev_file")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ts_jest_options(self) -> typing.Optional[TsJestOptions]:
        '''(experimental) Options for ts-jest.

        :stability: experimental
        '''
        result = self._values.get("ts_jest_options")
        return typing.cast(typing.Optional[TsJestOptions], result)

    @builtins.property
    def typescript_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) TypeScript version to use.

        NOTE: Typescript is not semantically versioned and should remain on the
        same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``).

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("typescript_version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TypeScriptProjectOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TypedocDocgen(
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TypedocDocgen",
):
    '''(experimental) Adds a simple Typescript documentation generator.

    :stability: experimental
    '''

    def __init__(self, project: TypeScriptProject) -> None:
        '''
        :param project: -

        :stability: experimental
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__05c2a64cbf1d03e81be8fd637cc486671fa9c1ee8abae939265da1f9e27dcc63)
            check_type(argname="argument project", value=project, expected_type=type_hints["project"])
        jsii.create(self.__class__, self, [project])


class TypeScriptAppProject(
    TypeScriptProject,
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TypeScriptAppProject",
):
    '''(experimental) TypeScript app.

    :stability: experimental
    :pjid: typescript-app
    '''

    def __init__(
        self,
        *,
        disable_tsconfig: typing.Optional[builtins.bool] = None,
        disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
        docgen: typing.Optional[builtins.bool] = None,
        docs_directory: typing.Optional[builtins.str] = None,
        entrypoint_types: typing.Optional[builtins.str] = None,
        eslint: typing.Optional[builtins.bool] = None,
        eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
        libdir: typing.Optional[builtins.str] = None,
        projenrc_ts: typing.Optional[builtins.bool] = None,
        projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        sample_code: typing.Optional[builtins.bool] = None,
        srcdir: typing.Optional[builtins.str] = None,
        testdir: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev_file: typing.Optional[builtins.str] = None,
        ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        typescript_version: typing.Optional[builtins.str] = None,
        default_release_branch: builtins.str,
        artifacts_directory: typing.Optional[builtins.str] = None,
        auto_approve_upgrades: typing.Optional[builtins.bool] = None,
        biome: typing.Optional[builtins.bool] = None,
        biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow: typing.Optional[builtins.bool] = None,
        build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
        bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
        check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
        code_cov: typing.Optional[builtins.bool] = None,
        code_cov_token_secret: typing.Optional[builtins.str] = None,
        copyright_owner: typing.Optional[builtins.str] = None,
        copyright_period: typing.Optional[builtins.str] = None,
        dependabot: typing.Optional[builtins.bool] = None,
        dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
        deps_upgrade: typing.Optional[builtins.bool] = None,
        deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
        gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        jest: typing.Optional[builtins.bool] = None,
        jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
        mutable_build: typing.Optional[builtins.bool] = None,
        npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        npmignore_enabled: typing.Optional[builtins.bool] = None,
        npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        package: typing.Optional[builtins.bool] = None,
        prettier: typing.Optional[builtins.bool] = None,
        prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_dev_dependency: typing.Optional[builtins.bool] = None,
        projenrc_js: typing.Optional[builtins.bool] = None,
        projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_version: typing.Optional[builtins.str] = None,
        pull_request_template: typing.Optional[builtins.bool] = None,
        pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
        release: typing.Optional[builtins.bool] = None,
        release_to_npm: typing.Optional[builtins.bool] = None,
        release_workflow: typing.Optional[builtins.bool] = None,
        workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
        workflow_node_version: typing.Optional[builtins.str] = None,
        workflow_package_cache: typing.Optional[builtins.bool] = None,
        auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_merge: typing.Optional[builtins.bool] = None,
        auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
        clobber: typing.Optional[builtins.bool] = None,
        dev_container: typing.Optional[builtins.bool] = None,
        github: typing.Optional[builtins.bool] = None,
        github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
        gitpod: typing.Optional[builtins.bool] = None,
        mergify: typing.Optional[builtins.bool] = None,
        mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
        project_type: typing.Optional[_ProjectType_fd80c725] = None,
        projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
        projen_token_secret: typing.Optional[builtins.str] = None,
        readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
        stale: typing.Optional[builtins.bool] = None,
        stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
        vscode: typing.Optional[builtins.bool] = None,
        allow_library_dependencies: typing.Optional[builtins.bool] = None,
        author_email: typing.Optional[builtins.str] = None,
        author_name: typing.Optional[builtins.str] = None,
        author_organization: typing.Optional[builtins.bool] = None,
        author_url: typing.Optional[builtins.str] = None,
        auto_detect_bin: typing.Optional[builtins.bool] = None,
        bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        bugs_email: typing.Optional[builtins.str] = None,
        bugs_url: typing.Optional[builtins.str] = None,
        bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        bun_version: typing.Optional[builtins.str] = None,
        code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
        deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[builtins.str] = None,
        homepage: typing.Optional[builtins.str] = None,
        keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
        license: typing.Optional[builtins.str] = None,
        licensed: typing.Optional[builtins.bool] = None,
        max_node_version: typing.Optional[builtins.str] = None,
        min_node_version: typing.Optional[builtins.str] = None,
        npm_access: typing.Optional[_NpmAccess_134fa228] = None,
        npm_provenance: typing.Optional[builtins.bool] = None,
        npm_registry: typing.Optional[builtins.str] = None,
        npm_registry_url: typing.Optional[builtins.str] = None,
        npm_token_secret: typing.Optional[builtins.str] = None,
        npm_trusted_publishing: typing.Optional[builtins.bool] = None,
        package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
        package_name: typing.Optional[builtins.str] = None,
        peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
        peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        pnpm_version: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        repository_directory: typing.Optional[builtins.str] = None,
        scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
        scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        stability: typing.Optional[builtins.str] = None,
        yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
        bump_package: typing.Optional[builtins.str] = None,
        jsii_release_version: typing.Optional[builtins.str] = None,
        major_version: typing.Optional[jsii.Number] = None,
        min_major_version: typing.Optional[jsii.Number] = None,
        next_version_command: typing.Optional[builtins.str] = None,
        npm_dist_tag: typing.Optional[builtins.str] = None,
        post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        prerelease: typing.Optional[builtins.str] = None,
        publish_dry_run: typing.Optional[builtins.bool] = None,
        publish_tasks: typing.Optional[builtins.bool] = None,
        releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
        release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
        release_environment: typing.Optional[builtins.str] = None,
        release_every_commit: typing.Optional[builtins.bool] = None,
        release_failure_issue: typing.Optional[builtins.bool] = None,
        release_failure_issue_label: typing.Optional[builtins.str] = None,
        release_schedule: typing.Optional[builtins.str] = None,
        release_tag_prefix: typing.Optional[builtins.str] = None,
        release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
        release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        release_workflow_name: typing.Optional[builtins.str] = None,
        release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        workflow_container_image: typing.Optional[builtins.str] = None,
        workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
        workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
        name: builtins.str,
        commit_generated: typing.Optional[builtins.bool] = None,
        git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
        logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
        outdir: typing.Optional[builtins.str] = None,
        parent: typing.Optional[_Project_57d89203] = None,
        projen_command: typing.Optional[builtins.str] = None,
        projenrc_json: typing.Optional[builtins.bool] = None,
        projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
        renovatebot: typing.Optional[builtins.bool] = None,
        renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param disable_tsconfig: (experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler). Default: false
        :param disable_tsconfig_dev: (experimental) Do not generate a ``tsconfig.dev.json`` file. Default: false
        :param docgen: (experimental) Docgen by Typedoc. Default: false
        :param docs_directory: (experimental) Docs directory. Default: "docs"
        :param entrypoint_types: (experimental) The .d.ts file that includes the type declarations for this module. Default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)
        :param eslint: (experimental) Setup eslint. Default: - true, unless biome is enabled
        :param eslint_options: (experimental) Eslint options. Default: - opinionated default options
        :param libdir: (experimental) Typescript artifacts output directory. Default: "lib"
        :param projenrc_ts: (experimental) Use TypeScript for your projenrc file (``.projenrc.ts``). Default: false
        :param projenrc_ts_options: (experimental) Options for .projenrc.ts.
        :param sample_code: (experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there. Default: true
        :param srcdir: (experimental) Typescript sources directory. Default: "src"
        :param testdir: (experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``. If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``), then tests are going to be compiled into ``lib/`` and executed as javascript. If the test directory is outside of ``src``, then we configure jest to compile the code in-memory. Default: "test"
        :param tsconfig: (experimental) Custom TSConfig. Default: - default options
        :param tsconfig_dev: (experimental) Custom tsconfig options for the development tsconfig.json file (used for testing). Default: - use the production tsconfig options
        :param tsconfig_dev_file: (experimental) The name of the development tsconfig.json file. Default: "tsconfig.dev.json"
        :param ts_jest_options: (experimental) Options for ts-jest.
        :param typescript_version: (experimental) TypeScript version to use. NOTE: Typescript is not semantically versioned and should remain on the same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``). Default: "latest"
        :param default_release_branch: (experimental) The name of the main release branch. Default: "main"
        :param artifacts_directory: (experimental) A directory which will contain build artifacts. Default: "dist"
        :param auto_approve_upgrades: (experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued). Throw if set to true but ``autoApproveOptions`` are not defined. Default: - true
        :param biome: (experimental) Setup Biome. Default: false
        :param biome_options: (experimental) Biome options. Default: - default options
        :param build_workflow: (experimental) Define a GitHub workflow for building PRs. Default: - true if not a subproject
        :param build_workflow_options: (experimental) Options for PR build workflow.
        :param build_workflow_triggers: (deprecated) Build workflow triggers. Default: "{ pullRequest: {}, workflowDispatch: {} }"
        :param bundler_options: (experimental) Options for ``Bundler``.
        :param check_licenses: (experimental) Configure which licenses should be deemed acceptable for use by dependencies. This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered. Default: - no license checks are run during the build and all licenses will be accepted
        :param code_cov: (experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``. Default: false
        :param code_cov_token_secret: (experimental) Define the secret name for a specified https://codecov.io/ token. Default: - OIDC auth is used
        :param copyright_owner: (experimental) License copyright owner. Default: - defaults to the value of authorName or "" if ``authorName`` is undefined.
        :param copyright_period: (experimental) The copyright years to put in the LICENSE file. Default: - current year
        :param dependabot: (experimental) Use dependabot to handle dependency upgrades. Cannot be used in conjunction with ``depsUpgrade``. Default: false
        :param dependabot_options: (experimental) Options for dependabot. Default: - default options
        :param deps_upgrade: (experimental) Use tasks and github workflows to handle dependency upgrades. Cannot be used in conjunction with ``dependabot``. Default: true
        :param deps_upgrade_options: (experimental) Options for ``UpgradeDependencies``. Default: - default options
        :param gitignore: (experimental) Additional entries to .gitignore.
        :param jest: (experimental) Setup jest unit tests. Default: true
        :param jest_options: (experimental) Jest options. Default: - default options
        :param mutable_build: (deprecated) Automatically update files modified during builds to pull-request branches. This means that any files synthesized by projen or e.g. test snapshots will always be up-to-date before a PR is merged. Implies that PR builds do not have anti-tamper checks. Default: true
        :param npmignore: (deprecated) Additional entries to .npmignore.
        :param npmignore_enabled: (experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs. Default: true
        :param npm_ignore_options: (experimental) Configuration options for .npmignore file.
        :param package: (experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``). Default: true
        :param prettier: (experimental) Setup prettier. Default: false
        :param prettier_options: (experimental) Prettier options. Default: - default options
        :param projen_dev_dependency: (experimental) Indicates of "projen" should be installed as a devDependency. Default: - true if not a subproject
        :param projenrc_js: (experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation. Default: - true if projenrcJson is false
        :param projenrc_js_options: (experimental) Options for .projenrc.js. Default: - default options
        :param projen_version: (experimental) Version of projen to install. Default: - Defaults to the latest version.
        :param pull_request_template: (experimental) Include a GitHub pull request template. Default: true
        :param pull_request_template_contents: (experimental) The contents of the pull request template. Default: - default content
        :param release: (experimental) Add release management to this project. Default: - true (false for subprojects)
        :param release_to_npm: (experimental) Automatically release to npm when new versions are introduced. Default: false
        :param release_workflow: (deprecated) DEPRECATED: renamed to ``release``. Default: - true if not a subproject
        :param workflow_bootstrap_steps: (experimental) Workflow steps to use in order to bootstrap this repo. Default: "yarn install --frozen-lockfile && yarn projen"
        :param workflow_git_identity: (experimental) The git identity to use in workflows. Default: - default GitHub Actions user
        :param workflow_node_version: (experimental) The node version used in GitHub Actions workflows. Always use this option if your GitHub Actions workflows require a specific to run. Default: - ``minNodeVersion`` if set, otherwise ``lts/*``.
        :param workflow_package_cache: (experimental) Enable Node.js package cache in GitHub workflows. Default: false
        :param auto_approve_options: (experimental) Enable and configure the 'auto approve' workflow. Default: - auto approve is disabled
        :param auto_merge: (experimental) Enable automatic merging on GitHub. Has no effect if ``github.mergify`` is set to false. Default: true
        :param auto_merge_options: (experimental) Configure options for automatic merging on GitHub. Has no effect if ``github.mergify`` or ``autoMerge`` is set to false. Default: - see defaults in ``AutoMergeOptions``
        :param clobber: (experimental) Add a ``clobber`` task which resets the repo to origin. Default: - true, but false for subprojects
        :param dev_container: (experimental) Add a VSCode development environment (used for GitHub Codespaces). Default: false
        :param github: (experimental) Enable GitHub integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param github_options: (experimental) Options for GitHub integration. Default: - see GitHubOptions
        :param gitpod: (experimental) Add a Gitpod development environment. Default: false
        :param mergify: (deprecated) Whether mergify should be enabled on this repository or not. Default: true
        :param mergify_options: (deprecated) Options for mergify. Default: - default options
        :param project_type: (deprecated) Which type of project this is (library/app). Default: ProjectType.UNKNOWN
        :param projen_credentials: (experimental) Choose a method of providing GitHub API access for projen workflows. Default: - use a personal access token named PROJEN_GITHUB_TOKEN
        :param projen_token_secret: (deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows. This token needs to have the ``repo``, ``workflows`` and ``packages`` scope. Default: "PROJEN_GITHUB_TOKEN"
        :param readme: (experimental) The README setup. Default: - { filename: 'README.md', contents: '# replace this' }
        :param stale: (experimental) Auto-close of stale issues and pull request. See ``staleOptions`` for options. Default: false
        :param stale_options: (experimental) Auto-close stale issues and pull requests. To disable set ``stale`` to ``false``. Default: - see defaults in ``StaleOptions``
        :param vscode: (experimental) Enable VSCode integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param allow_library_dependencies: (experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``. This is normally only allowed for libraries. For apps, there's no meaning for specifying these. Default: true
        :param author_email: (experimental) Author's e-mail.
        :param author_name: (experimental) Author's name.
        :param author_organization: (experimental) Is the author an organization.
        :param author_url: (experimental) Author's URL / Website.
        :param auto_detect_bin: (experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section. Default: true
        :param bin: (experimental) Binary programs vended with your module. You can use this option to add/customize how binaries are represented in your ``package.json``, but unless ``autoDetectBin`` is ``false``, every executable file under ``bin`` will automatically be added to this section.
        :param bugs_email: (experimental) The email address to which issues should be reported.
        :param bugs_url: (experimental) The url to your project's issue tracker.
        :param bundled_deps: (experimental) List of dependencies to bundle into this module. These modules will be added both to the ``dependencies`` section and ``bundledDependencies`` section of your ``package.json``. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include.
        :param bun_version: (experimental) The version of Bun to use if using Bun as a package manager. Default: "latest"
        :param code_artifact_options: (experimental) Options for npm packages using AWS CodeArtifact. This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact Default: - undefined
        :param deps: (experimental) Runtime dependencies of this module. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param description: (experimental) The description is just a string that helps people understand the purpose of the package. It can be used when searching for packages in a package manager as well. See https://classic.yarnpkg.com/en/docs/package-json/#toc-description
        :param dev_deps: (experimental) Build dependencies for this module. These dependencies will only be available in your build environment but will not be fetched when this module is consumed. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param entrypoint: (experimental) Module entrypoint (``main`` in ``package.json``). Set to an empty string to not include ``main`` in your package.json Default: "lib/index.js"
        :param homepage: (experimental) Package's Homepage / Website.
        :param keywords: (experimental) Keywords to include in ``package.json``.
        :param license: (experimental) License's SPDX identifier. See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses. Use the ``licensed`` option if you want to no license to be specified. Default: "Apache-2.0"
        :param licensed: (experimental) Indicates if a license should be added. Default: true
        :param max_node_version: (experimental) The maximum node version supported by this package. Most projects should not use this option. The value indicates that the package is incompatible with any newer versions of node. This requirement is enforced via the engines field. You will normally not need to set this option. Consider this option only if your package is known to not function with newer versions of node. Default: - no maximum version is enforced
        :param min_node_version: (experimental) The minimum node version required by this package to function. Most projects should not use this option. The value indicates that the package is incompatible with any older versions of node. This requirement is enforced via the engines field. You will normally not need to set this option, even if your package is incompatible with EOL versions of node. Consider this option only if your package depends on a specific feature, that is not available in other LTS versions. Setting this option has very high impact on the consumers of your package, as package managers will actively prevent usage with node versions you have marked as incompatible. To change the node version of your CI/CD workflows, use ``workflowNodeVersion``. Default: - no minimum version is enforced
        :param npm_access: (experimental) Access level of the npm package. Default: - for scoped packages (e.g. ``foo@bar``), the default is ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is ``NpmAccess.PUBLIC``.
        :param npm_provenance: (experimental) Should provenance statements be generated when the package is published. A supported package manager is required to publish a package with npm provenance statements and you will need to use a supported CI/CD provider. Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages, which is using npm internally and supports provenance statements independently of the package manager used. Default: - true for public packages, false otherwise
        :param npm_registry: (deprecated) The host name of the npm registry to publish to. Cannot be set together with ``npmRegistryUrl``.
        :param npm_registry_url: (experimental) The base URL of the npm package registry. Must be a URL (e.g. start with "https://" or "http://") Default: "https://registry.npmjs.org"
        :param npm_token_secret: (experimental) GitHub secret which contains the NPM token to use when publishing packages. Default: "NPM_TOKEN"
        :param npm_trusted_publishing: (experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work. Default: - false
        :param package_manager: (experimental) The Node Package Manager used to execute scripts. Default: NodePackageManager.YARN_CLASSIC
        :param package_name: (experimental) The "name" in package.json. Default: - defaults to project name
        :param peer_dependency_options: (experimental) Options for ``peerDeps``.
        :param peer_deps: (experimental) Peer dependencies for this module. Dependencies listed here are required to be installed (and satisfied) by the *consumer* of this library. Using peer dependencies allows you to ensure that only a single module of a certain library exists in the ``node_modules`` tree of your consumers. Note that prior to npm@7, peer dependencies are *not* automatically installed, which means that adding peer dependencies to a library will be a breaking change for your customers. Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is enabled by default), projen will automatically add a dev dependency with a pinned version for each peer dependency. This will ensure that you build & test your module against the lowest peer version required. Default: []
        :param pnpm_version: (experimental) The version of PNPM to use if using PNPM as a package manager. Default: "9"
        :param repository: (experimental) The repository is the location where the actual code for your package lives. See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository
        :param repository_directory: (experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.
        :param scoped_packages_options: (experimental) Options for privately hosted scoped packages. Default: - fetch all scoped packages from the public npm registry
        :param scripts: (deprecated) npm scripts to include. If a script has the same name as a standard script, the standard script will be overwritten. Also adds the script as a task. Default: {}
        :param stability: (experimental) Package's Stability.
        :param yarn_berry_options: (experimental) Options for Yarn Berry. Default: - Yarn Berry v4 with all default options
        :param bump_package: (experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string. This can be any compatible package version, including the deprecated ``standard-version@9``. Default: - A recent version of "commit-and-tag-version"
        :param jsii_release_version: (experimental) Version requirement of ``publib`` which is used to publish modules to npm. Default: "latest"
        :param major_version: (experimental) Major version to release from the default branch. If this is specified, we bump the latest version of this major version line. If not specified, we bump the global latest version. Default: - Major version is not enforced.
        :param min_major_version: (experimental) Minimal Major version to release. This can be useful to set to 1, as breaking changes before the 1.x major release are not incrementing the major version number. Can not be set together with ``majorVersion``. Default: - No minimum version is being enforced
        :param next_version_command: (experimental) A shell command to control the next version to release. If present, this shell command will be run before the bump is executed, and it determines what version to release. It will be executed in the following environment: - Working directory: the project directory. - ``$VERSION``: the current version. Looks like ``1.2.3``. - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset. - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``. The command should print one of the following to ``stdout``: - Nothing: the next version number will be determined based on commit history. - ``x.y.z``: the next version number will be ``x.y.z``. - ``major|minor|patch``: the next version number will be the current version number with the indicated component bumped. This setting cannot be specified together with ``minMajorVersion``; the invoked script can be used to achieve the effects of ``minMajorVersion``. Default: - The next version will be determined based on the commit history and project settings.
        :param npm_dist_tag: (experimental) The npmDistTag to use when publishing from the default branch. To set the npm dist-tag for release branches, set the ``npmDistTag`` property for each branch. Default: "latest"
        :param post_build_steps: (experimental) Steps to execute after build as part of the release workflow. Default: []
        :param prerelease: (experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre"). Default: - normal semantic versions
        :param publish_dry_run: (experimental) Instead of actually publishing to package managers, just print the publishing command. Default: false
        :param publish_tasks: (experimental) Define publishing tasks that can be executed manually as well as workflows. Normally, publishing only happens within automated workflows. Enable this in order to create a publishing task for each publishing activity. Default: false
        :param releasable_commits: (experimental) Find commits that should be considered releasable Used to decide if a release is required. Default: ReleasableCommits.everyCommit()
        :param release_branches: (experimental) Defines additional release branches. A workflow will be created for each release branch which will publish releases from commits in this branch. Each release branch *must* be assigned a major version number which is used to enforce that versions published from that branch always use that major version. If multiple branches are used, the ``majorVersion`` field must also be provided for the default branch. Default: - no additional branches are used for release. you can use ``addBranch()`` to add additional branches.
        :param release_environment: (experimental) The GitHub Actions environment used for the release. This can be used to add an explicit approval step to the release or limit who can initiate a release through environment protection rules. When multiple artifacts are released, the environment can be overwritten on a per artifact basis. Default: - no environment used, unless set at the artifact level
        :param release_every_commit: (deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``. Default: true
        :param release_failure_issue: (experimental) Create a github issue on every failed publishing task. Default: false
        :param release_failure_issue_label: (experimental) The label to apply to issues indicating publish failures. Only applies if ``releaseFailureIssue`` is true. Default: "failed-release"
        :param release_schedule: (deprecated) CRON schedule to trigger new releases. Default: - no scheduled releases
        :param release_tag_prefix: (experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers. Note: this prefix is used to detect the latest tagged version when bumping, so if you change this on a project with an existing version history, you may need to manually tag your latest release with the new prefix. Default: "v"
        :param release_trigger: (experimental) The release trigger to use. Default: - Continuous releases (``ReleaseTrigger.continuous()``)
        :param release_workflow_env: (experimental) Build environment variables for release workflows. Default: {}
        :param release_workflow_name: (experimental) The name of the default release workflow. Default: "release"
        :param release_workflow_setup_steps: (experimental) A set of workflow steps to execute in order to setup the workflow container.
        :param versionrc_options: (experimental) Custom configuration used when creating changelog with commit-and-tag-version package. Given values either append to default configuration or overwrite values in it. Default: - standard configuration applicable for GitHub repositories
        :param workflow_container_image: (experimental) Container image to use for GitHub workflows. Default: - default image
        :param workflow_runs_on: (experimental) Github Runner selection labels. Default: ["ubuntu-latest"]
        :param workflow_runs_on_group: (experimental) Github Runner Group selection options.
        :param name: (experimental) This is the name of your project. Default: $BASEDIR
        :param commit_generated: (experimental) Whether to commit the managed files by default. Default: true
        :param git_ignore_options: (experimental) Configuration options for .gitignore file.
        :param git_options: (experimental) Configuration options for git.
        :param logging: (experimental) Configure logging options such as verbosity. Default: {}
        :param outdir: (experimental) The root directory of the project. Relative to this directory, all files are synthesized. If this project has a parent, this directory is relative to the parent directory and it cannot be the same as the parent or any of it's other subprojects. Default: "."
        :param parent: (experimental) The parent project, if this project is part of a bigger project.
        :param projen_command: (experimental) The shell command to use in order to run the projen CLI. Can be used to customize in special environments. Default: "npx projen"
        :param projenrc_json: (experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation. Default: false
        :param projenrc_json_options: (experimental) Options for .projenrc.json. Default: - default options
        :param renovatebot: (experimental) Use renovatebot to handle dependency upgrades. Default: false
        :param renovatebot_options: (experimental) Options for renovatebot. Default: - default options

        :stability: experimental
        '''
        options = TypeScriptProjectOptions(
            disable_tsconfig=disable_tsconfig,
            disable_tsconfig_dev=disable_tsconfig_dev,
            docgen=docgen,
            docs_directory=docs_directory,
            entrypoint_types=entrypoint_types,
            eslint=eslint,
            eslint_options=eslint_options,
            libdir=libdir,
            projenrc_ts=projenrc_ts,
            projenrc_ts_options=projenrc_ts_options,
            sample_code=sample_code,
            srcdir=srcdir,
            testdir=testdir,
            tsconfig=tsconfig,
            tsconfig_dev=tsconfig_dev,
            tsconfig_dev_file=tsconfig_dev_file,
            ts_jest_options=ts_jest_options,
            typescript_version=typescript_version,
            default_release_branch=default_release_branch,
            artifacts_directory=artifacts_directory,
            auto_approve_upgrades=auto_approve_upgrades,
            biome=biome,
            biome_options=biome_options,
            build_workflow=build_workflow,
            build_workflow_options=build_workflow_options,
            build_workflow_triggers=build_workflow_triggers,
            bundler_options=bundler_options,
            check_licenses=check_licenses,
            code_cov=code_cov,
            code_cov_token_secret=code_cov_token_secret,
            copyright_owner=copyright_owner,
            copyright_period=copyright_period,
            dependabot=dependabot,
            dependabot_options=dependabot_options,
            deps_upgrade=deps_upgrade,
            deps_upgrade_options=deps_upgrade_options,
            gitignore=gitignore,
            jest=jest,
            jest_options=jest_options,
            mutable_build=mutable_build,
            npmignore=npmignore,
            npmignore_enabled=npmignore_enabled,
            npm_ignore_options=npm_ignore_options,
            package=package,
            prettier=prettier,
            prettier_options=prettier_options,
            projen_dev_dependency=projen_dev_dependency,
            projenrc_js=projenrc_js,
            projenrc_js_options=projenrc_js_options,
            projen_version=projen_version,
            pull_request_template=pull_request_template,
            pull_request_template_contents=pull_request_template_contents,
            release=release,
            release_to_npm=release_to_npm,
            release_workflow=release_workflow,
            workflow_bootstrap_steps=workflow_bootstrap_steps,
            workflow_git_identity=workflow_git_identity,
            workflow_node_version=workflow_node_version,
            workflow_package_cache=workflow_package_cache,
            auto_approve_options=auto_approve_options,
            auto_merge=auto_merge,
            auto_merge_options=auto_merge_options,
            clobber=clobber,
            dev_container=dev_container,
            github=github,
            github_options=github_options,
            gitpod=gitpod,
            mergify=mergify,
            mergify_options=mergify_options,
            project_type=project_type,
            projen_credentials=projen_credentials,
            projen_token_secret=projen_token_secret,
            readme=readme,
            stale=stale,
            stale_options=stale_options,
            vscode=vscode,
            allow_library_dependencies=allow_library_dependencies,
            author_email=author_email,
            author_name=author_name,
            author_organization=author_organization,
            author_url=author_url,
            auto_detect_bin=auto_detect_bin,
            bin=bin,
            bugs_email=bugs_email,
            bugs_url=bugs_url,
            bundled_deps=bundled_deps,
            bun_version=bun_version,
            code_artifact_options=code_artifact_options,
            deps=deps,
            description=description,
            dev_deps=dev_deps,
            entrypoint=entrypoint,
            homepage=homepage,
            keywords=keywords,
            license=license,
            licensed=licensed,
            max_node_version=max_node_version,
            min_node_version=min_node_version,
            npm_access=npm_access,
            npm_provenance=npm_provenance,
            npm_registry=npm_registry,
            npm_registry_url=npm_registry_url,
            npm_token_secret=npm_token_secret,
            npm_trusted_publishing=npm_trusted_publishing,
            package_manager=package_manager,
            package_name=package_name,
            peer_dependency_options=peer_dependency_options,
            peer_deps=peer_deps,
            pnpm_version=pnpm_version,
            repository=repository,
            repository_directory=repository_directory,
            scoped_packages_options=scoped_packages_options,
            scripts=scripts,
            stability=stability,
            yarn_berry_options=yarn_berry_options,
            bump_package=bump_package,
            jsii_release_version=jsii_release_version,
            major_version=major_version,
            min_major_version=min_major_version,
            next_version_command=next_version_command,
            npm_dist_tag=npm_dist_tag,
            post_build_steps=post_build_steps,
            prerelease=prerelease,
            publish_dry_run=publish_dry_run,
            publish_tasks=publish_tasks,
            releasable_commits=releasable_commits,
            release_branches=release_branches,
            release_environment=release_environment,
            release_every_commit=release_every_commit,
            release_failure_issue=release_failure_issue,
            release_failure_issue_label=release_failure_issue_label,
            release_schedule=release_schedule,
            release_tag_prefix=release_tag_prefix,
            release_trigger=release_trigger,
            release_workflow_env=release_workflow_env,
            release_workflow_name=release_workflow_name,
            release_workflow_setup_steps=release_workflow_setup_steps,
            versionrc_options=versionrc_options,
            workflow_container_image=workflow_container_image,
            workflow_runs_on=workflow_runs_on,
            workflow_runs_on_group=workflow_runs_on_group,
            name=name,
            commit_generated=commit_generated,
            git_ignore_options=git_ignore_options,
            git_options=git_options,
            logging=logging,
            outdir=outdir,
            parent=parent,
            projen_command=projen_command,
            projenrc_json=projenrc_json,
            projenrc_json_options=projenrc_json_options,
            renovatebot=renovatebot,
            renovatebot_options=renovatebot_options,
        )

        jsii.create(self.__class__, self, [options])


class TypeScriptLibraryProject(
    TypeScriptProject,
    metaclass=jsii.JSIIMeta,
    jsii_type="projen.typescript.TypeScriptLibraryProject",
):
    '''
    :deprecated: use ``TypeScriptProject``

    :stability: deprecated
    '''

    def __init__(
        self,
        *,
        disable_tsconfig: typing.Optional[builtins.bool] = None,
        disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
        docgen: typing.Optional[builtins.bool] = None,
        docs_directory: typing.Optional[builtins.str] = None,
        entrypoint_types: typing.Optional[builtins.str] = None,
        eslint: typing.Optional[builtins.bool] = None,
        eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
        libdir: typing.Optional[builtins.str] = None,
        projenrc_ts: typing.Optional[builtins.bool] = None,
        projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        sample_code: typing.Optional[builtins.bool] = None,
        srcdir: typing.Optional[builtins.str] = None,
        testdir: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev_file: typing.Optional[builtins.str] = None,
        ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        typescript_version: typing.Optional[builtins.str] = None,
        default_release_branch: builtins.str,
        artifacts_directory: typing.Optional[builtins.str] = None,
        auto_approve_upgrades: typing.Optional[builtins.bool] = None,
        biome: typing.Optional[builtins.bool] = None,
        biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow: typing.Optional[builtins.bool] = None,
        build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
        bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
        check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
        code_cov: typing.Optional[builtins.bool] = None,
        code_cov_token_secret: typing.Optional[builtins.str] = None,
        copyright_owner: typing.Optional[builtins.str] = None,
        copyright_period: typing.Optional[builtins.str] = None,
        dependabot: typing.Optional[builtins.bool] = None,
        dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
        deps_upgrade: typing.Optional[builtins.bool] = None,
        deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
        gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        jest: typing.Optional[builtins.bool] = None,
        jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
        mutable_build: typing.Optional[builtins.bool] = None,
        npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        npmignore_enabled: typing.Optional[builtins.bool] = None,
        npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        package: typing.Optional[builtins.bool] = None,
        prettier: typing.Optional[builtins.bool] = None,
        prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_dev_dependency: typing.Optional[builtins.bool] = None,
        projenrc_js: typing.Optional[builtins.bool] = None,
        projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_version: typing.Optional[builtins.str] = None,
        pull_request_template: typing.Optional[builtins.bool] = None,
        pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
        release: typing.Optional[builtins.bool] = None,
        release_to_npm: typing.Optional[builtins.bool] = None,
        release_workflow: typing.Optional[builtins.bool] = None,
        workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
        workflow_node_version: typing.Optional[builtins.str] = None,
        workflow_package_cache: typing.Optional[builtins.bool] = None,
        auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_merge: typing.Optional[builtins.bool] = None,
        auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
        clobber: typing.Optional[builtins.bool] = None,
        dev_container: typing.Optional[builtins.bool] = None,
        github: typing.Optional[builtins.bool] = None,
        github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
        gitpod: typing.Optional[builtins.bool] = None,
        mergify: typing.Optional[builtins.bool] = None,
        mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
        project_type: typing.Optional[_ProjectType_fd80c725] = None,
        projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
        projen_token_secret: typing.Optional[builtins.str] = None,
        readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
        stale: typing.Optional[builtins.bool] = None,
        stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
        vscode: typing.Optional[builtins.bool] = None,
        allow_library_dependencies: typing.Optional[builtins.bool] = None,
        author_email: typing.Optional[builtins.str] = None,
        author_name: typing.Optional[builtins.str] = None,
        author_organization: typing.Optional[builtins.bool] = None,
        author_url: typing.Optional[builtins.str] = None,
        auto_detect_bin: typing.Optional[builtins.bool] = None,
        bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        bugs_email: typing.Optional[builtins.str] = None,
        bugs_url: typing.Optional[builtins.str] = None,
        bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        bun_version: typing.Optional[builtins.str] = None,
        code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
        deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[builtins.str] = None,
        homepage: typing.Optional[builtins.str] = None,
        keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
        license: typing.Optional[builtins.str] = None,
        licensed: typing.Optional[builtins.bool] = None,
        max_node_version: typing.Optional[builtins.str] = None,
        min_node_version: typing.Optional[builtins.str] = None,
        npm_access: typing.Optional[_NpmAccess_134fa228] = None,
        npm_provenance: typing.Optional[builtins.bool] = None,
        npm_registry: typing.Optional[builtins.str] = None,
        npm_registry_url: typing.Optional[builtins.str] = None,
        npm_token_secret: typing.Optional[builtins.str] = None,
        npm_trusted_publishing: typing.Optional[builtins.bool] = None,
        package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
        package_name: typing.Optional[builtins.str] = None,
        peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
        peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        pnpm_version: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        repository_directory: typing.Optional[builtins.str] = None,
        scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
        scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        stability: typing.Optional[builtins.str] = None,
        yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
        bump_package: typing.Optional[builtins.str] = None,
        jsii_release_version: typing.Optional[builtins.str] = None,
        major_version: typing.Optional[jsii.Number] = None,
        min_major_version: typing.Optional[jsii.Number] = None,
        next_version_command: typing.Optional[builtins.str] = None,
        npm_dist_tag: typing.Optional[builtins.str] = None,
        post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        prerelease: typing.Optional[builtins.str] = None,
        publish_dry_run: typing.Optional[builtins.bool] = None,
        publish_tasks: typing.Optional[builtins.bool] = None,
        releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
        release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
        release_environment: typing.Optional[builtins.str] = None,
        release_every_commit: typing.Optional[builtins.bool] = None,
        release_failure_issue: typing.Optional[builtins.bool] = None,
        release_failure_issue_label: typing.Optional[builtins.str] = None,
        release_schedule: typing.Optional[builtins.str] = None,
        release_tag_prefix: typing.Optional[builtins.str] = None,
        release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
        release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        release_workflow_name: typing.Optional[builtins.str] = None,
        release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        workflow_container_image: typing.Optional[builtins.str] = None,
        workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
        workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
        name: builtins.str,
        commit_generated: typing.Optional[builtins.bool] = None,
        git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
        logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
        outdir: typing.Optional[builtins.str] = None,
        parent: typing.Optional[_Project_57d89203] = None,
        projen_command: typing.Optional[builtins.str] = None,
        projenrc_json: typing.Optional[builtins.bool] = None,
        projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
        renovatebot: typing.Optional[builtins.bool] = None,
        renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param disable_tsconfig: (experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler). Default: false
        :param disable_tsconfig_dev: (experimental) Do not generate a ``tsconfig.dev.json`` file. Default: false
        :param docgen: (experimental) Docgen by Typedoc. Default: false
        :param docs_directory: (experimental) Docs directory. Default: "docs"
        :param entrypoint_types: (experimental) The .d.ts file that includes the type declarations for this module. Default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)
        :param eslint: (experimental) Setup eslint. Default: - true, unless biome is enabled
        :param eslint_options: (experimental) Eslint options. Default: - opinionated default options
        :param libdir: (experimental) Typescript artifacts output directory. Default: "lib"
        :param projenrc_ts: (experimental) Use TypeScript for your projenrc file (``.projenrc.ts``). Default: false
        :param projenrc_ts_options: (experimental) Options for .projenrc.ts.
        :param sample_code: (experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there. Default: true
        :param srcdir: (experimental) Typescript sources directory. Default: "src"
        :param testdir: (experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``. If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``), then tests are going to be compiled into ``lib/`` and executed as javascript. If the test directory is outside of ``src``, then we configure jest to compile the code in-memory. Default: "test"
        :param tsconfig: (experimental) Custom TSConfig. Default: - default options
        :param tsconfig_dev: (experimental) Custom tsconfig options for the development tsconfig.json file (used for testing). Default: - use the production tsconfig options
        :param tsconfig_dev_file: (experimental) The name of the development tsconfig.json file. Default: "tsconfig.dev.json"
        :param ts_jest_options: (experimental) Options for ts-jest.
        :param typescript_version: (experimental) TypeScript version to use. NOTE: Typescript is not semantically versioned and should remain on the same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``). Default: "latest"
        :param default_release_branch: (experimental) The name of the main release branch. Default: "main"
        :param artifacts_directory: (experimental) A directory which will contain build artifacts. Default: "dist"
        :param auto_approve_upgrades: (experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued). Throw if set to true but ``autoApproveOptions`` are not defined. Default: - true
        :param biome: (experimental) Setup Biome. Default: false
        :param biome_options: (experimental) Biome options. Default: - default options
        :param build_workflow: (experimental) Define a GitHub workflow for building PRs. Default: - true if not a subproject
        :param build_workflow_options: (experimental) Options for PR build workflow.
        :param build_workflow_triggers: (deprecated) Build workflow triggers. Default: "{ pullRequest: {}, workflowDispatch: {} }"
        :param bundler_options: (experimental) Options for ``Bundler``.
        :param check_licenses: (experimental) Configure which licenses should be deemed acceptable for use by dependencies. This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered. Default: - no license checks are run during the build and all licenses will be accepted
        :param code_cov: (experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``. Default: false
        :param code_cov_token_secret: (experimental) Define the secret name for a specified https://codecov.io/ token. Default: - OIDC auth is used
        :param copyright_owner: (experimental) License copyright owner. Default: - defaults to the value of authorName or "" if ``authorName`` is undefined.
        :param copyright_period: (experimental) The copyright years to put in the LICENSE file. Default: - current year
        :param dependabot: (experimental) Use dependabot to handle dependency upgrades. Cannot be used in conjunction with ``depsUpgrade``. Default: false
        :param dependabot_options: (experimental) Options for dependabot. Default: - default options
        :param deps_upgrade: (experimental) Use tasks and github workflows to handle dependency upgrades. Cannot be used in conjunction with ``dependabot``. Default: true
        :param deps_upgrade_options: (experimental) Options for ``UpgradeDependencies``. Default: - default options
        :param gitignore: (experimental) Additional entries to .gitignore.
        :param jest: (experimental) Setup jest unit tests. Default: true
        :param jest_options: (experimental) Jest options. Default: - default options
        :param mutable_build: (deprecated) Automatically update files modified during builds to pull-request branches. This means that any files synthesized by projen or e.g. test snapshots will always be up-to-date before a PR is merged. Implies that PR builds do not have anti-tamper checks. Default: true
        :param npmignore: (deprecated) Additional entries to .npmignore.
        :param npmignore_enabled: (experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs. Default: true
        :param npm_ignore_options: (experimental) Configuration options for .npmignore file.
        :param package: (experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``). Default: true
        :param prettier: (experimental) Setup prettier. Default: false
        :param prettier_options: (experimental) Prettier options. Default: - default options
        :param projen_dev_dependency: (experimental) Indicates of "projen" should be installed as a devDependency. Default: - true if not a subproject
        :param projenrc_js: (experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation. Default: - true if projenrcJson is false
        :param projenrc_js_options: (experimental) Options for .projenrc.js. Default: - default options
        :param projen_version: (experimental) Version of projen to install. Default: - Defaults to the latest version.
        :param pull_request_template: (experimental) Include a GitHub pull request template. Default: true
        :param pull_request_template_contents: (experimental) The contents of the pull request template. Default: - default content
        :param release: (experimental) Add release management to this project. Default: - true (false for subprojects)
        :param release_to_npm: (experimental) Automatically release to npm when new versions are introduced. Default: false
        :param release_workflow: (deprecated) DEPRECATED: renamed to ``release``. Default: - true if not a subproject
        :param workflow_bootstrap_steps: (experimental) Workflow steps to use in order to bootstrap this repo. Default: "yarn install --frozen-lockfile && yarn projen"
        :param workflow_git_identity: (experimental) The git identity to use in workflows. Default: - default GitHub Actions user
        :param workflow_node_version: (experimental) The node version used in GitHub Actions workflows. Always use this option if your GitHub Actions workflows require a specific to run. Default: - ``minNodeVersion`` if set, otherwise ``lts/*``.
        :param workflow_package_cache: (experimental) Enable Node.js package cache in GitHub workflows. Default: false
        :param auto_approve_options: (experimental) Enable and configure the 'auto approve' workflow. Default: - auto approve is disabled
        :param auto_merge: (experimental) Enable automatic merging on GitHub. Has no effect if ``github.mergify`` is set to false. Default: true
        :param auto_merge_options: (experimental) Configure options for automatic merging on GitHub. Has no effect if ``github.mergify`` or ``autoMerge`` is set to false. Default: - see defaults in ``AutoMergeOptions``
        :param clobber: (experimental) Add a ``clobber`` task which resets the repo to origin. Default: - true, but false for subprojects
        :param dev_container: (experimental) Add a VSCode development environment (used for GitHub Codespaces). Default: false
        :param github: (experimental) Enable GitHub integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param github_options: (experimental) Options for GitHub integration. Default: - see GitHubOptions
        :param gitpod: (experimental) Add a Gitpod development environment. Default: false
        :param mergify: (deprecated) Whether mergify should be enabled on this repository or not. Default: true
        :param mergify_options: (deprecated) Options for mergify. Default: - default options
        :param project_type: (deprecated) Which type of project this is (library/app). Default: ProjectType.UNKNOWN
        :param projen_credentials: (experimental) Choose a method of providing GitHub API access for projen workflows. Default: - use a personal access token named PROJEN_GITHUB_TOKEN
        :param projen_token_secret: (deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows. This token needs to have the ``repo``, ``workflows`` and ``packages`` scope. Default: "PROJEN_GITHUB_TOKEN"
        :param readme: (experimental) The README setup. Default: - { filename: 'README.md', contents: '# replace this' }
        :param stale: (experimental) Auto-close of stale issues and pull request. See ``staleOptions`` for options. Default: false
        :param stale_options: (experimental) Auto-close stale issues and pull requests. To disable set ``stale`` to ``false``. Default: - see defaults in ``StaleOptions``
        :param vscode: (experimental) Enable VSCode integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param allow_library_dependencies: (experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``. This is normally only allowed for libraries. For apps, there's no meaning for specifying these. Default: true
        :param author_email: (experimental) Author's e-mail.
        :param author_name: (experimental) Author's name.
        :param author_organization: (experimental) Is the author an organization.
        :param author_url: (experimental) Author's URL / Website.
        :param auto_detect_bin: (experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section. Default: true
        :param bin: (experimental) Binary programs vended with your module. You can use this option to add/customize how binaries are represented in your ``package.json``, but unless ``autoDetectBin`` is ``false``, every executable file under ``bin`` will automatically be added to this section.
        :param bugs_email: (experimental) The email address to which issues should be reported.
        :param bugs_url: (experimental) The url to your project's issue tracker.
        :param bundled_deps: (experimental) List of dependencies to bundle into this module. These modules will be added both to the ``dependencies`` section and ``bundledDependencies`` section of your ``package.json``. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include.
        :param bun_version: (experimental) The version of Bun to use if using Bun as a package manager. Default: "latest"
        :param code_artifact_options: (experimental) Options for npm packages using AWS CodeArtifact. This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact Default: - undefined
        :param deps: (experimental) Runtime dependencies of this module. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param description: (experimental) The description is just a string that helps people understand the purpose of the package. It can be used when searching for packages in a package manager as well. See https://classic.yarnpkg.com/en/docs/package-json/#toc-description
        :param dev_deps: (experimental) Build dependencies for this module. These dependencies will only be available in your build environment but will not be fetched when this module is consumed. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param entrypoint: (experimental) Module entrypoint (``main`` in ``package.json``). Set to an empty string to not include ``main`` in your package.json Default: "lib/index.js"
        :param homepage: (experimental) Package's Homepage / Website.
        :param keywords: (experimental) Keywords to include in ``package.json``.
        :param license: (experimental) License's SPDX identifier. See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses. Use the ``licensed`` option if you want to no license to be specified. Default: "Apache-2.0"
        :param licensed: (experimental) Indicates if a license should be added. Default: true
        :param max_node_version: (experimental) The maximum node version supported by this package. Most projects should not use this option. The value indicates that the package is incompatible with any newer versions of node. This requirement is enforced via the engines field. You will normally not need to set this option. Consider this option only if your package is known to not function with newer versions of node. Default: - no maximum version is enforced
        :param min_node_version: (experimental) The minimum node version required by this package to function. Most projects should not use this option. The value indicates that the package is incompatible with any older versions of node. This requirement is enforced via the engines field. You will normally not need to set this option, even if your package is incompatible with EOL versions of node. Consider this option only if your package depends on a specific feature, that is not available in other LTS versions. Setting this option has very high impact on the consumers of your package, as package managers will actively prevent usage with node versions you have marked as incompatible. To change the node version of your CI/CD workflows, use ``workflowNodeVersion``. Default: - no minimum version is enforced
        :param npm_access: (experimental) Access level of the npm package. Default: - for scoped packages (e.g. ``foo@bar``), the default is ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is ``NpmAccess.PUBLIC``.
        :param npm_provenance: (experimental) Should provenance statements be generated when the package is published. A supported package manager is required to publish a package with npm provenance statements and you will need to use a supported CI/CD provider. Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages, which is using npm internally and supports provenance statements independently of the package manager used. Default: - true for public packages, false otherwise
        :param npm_registry: (deprecated) The host name of the npm registry to publish to. Cannot be set together with ``npmRegistryUrl``.
        :param npm_registry_url: (experimental) The base URL of the npm package registry. Must be a URL (e.g. start with "https://" or "http://") Default: "https://registry.npmjs.org"
        :param npm_token_secret: (experimental) GitHub secret which contains the NPM token to use when publishing packages. Default: "NPM_TOKEN"
        :param npm_trusted_publishing: (experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work. Default: - false
        :param package_manager: (experimental) The Node Package Manager used to execute scripts. Default: NodePackageManager.YARN_CLASSIC
        :param package_name: (experimental) The "name" in package.json. Default: - defaults to project name
        :param peer_dependency_options: (experimental) Options for ``peerDeps``.
        :param peer_deps: (experimental) Peer dependencies for this module. Dependencies listed here are required to be installed (and satisfied) by the *consumer* of this library. Using peer dependencies allows you to ensure that only a single module of a certain library exists in the ``node_modules`` tree of your consumers. Note that prior to npm@7, peer dependencies are *not* automatically installed, which means that adding peer dependencies to a library will be a breaking change for your customers. Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is enabled by default), projen will automatically add a dev dependency with a pinned version for each peer dependency. This will ensure that you build & test your module against the lowest peer version required. Default: []
        :param pnpm_version: (experimental) The version of PNPM to use if using PNPM as a package manager. Default: "9"
        :param repository: (experimental) The repository is the location where the actual code for your package lives. See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository
        :param repository_directory: (experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.
        :param scoped_packages_options: (experimental) Options for privately hosted scoped packages. Default: - fetch all scoped packages from the public npm registry
        :param scripts: (deprecated) npm scripts to include. If a script has the same name as a standard script, the standard script will be overwritten. Also adds the script as a task. Default: {}
        :param stability: (experimental) Package's Stability.
        :param yarn_berry_options: (experimental) Options for Yarn Berry. Default: - Yarn Berry v4 with all default options
        :param bump_package: (experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string. This can be any compatible package version, including the deprecated ``standard-version@9``. Default: - A recent version of "commit-and-tag-version"
        :param jsii_release_version: (experimental) Version requirement of ``publib`` which is used to publish modules to npm. Default: "latest"
        :param major_version: (experimental) Major version to release from the default branch. If this is specified, we bump the latest version of this major version line. If not specified, we bump the global latest version. Default: - Major version is not enforced.
        :param min_major_version: (experimental) Minimal Major version to release. This can be useful to set to 1, as breaking changes before the 1.x major release are not incrementing the major version number. Can not be set together with ``majorVersion``. Default: - No minimum version is being enforced
        :param next_version_command: (experimental) A shell command to control the next version to release. If present, this shell command will be run before the bump is executed, and it determines what version to release. It will be executed in the following environment: - Working directory: the project directory. - ``$VERSION``: the current version. Looks like ``1.2.3``. - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset. - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``. The command should print one of the following to ``stdout``: - Nothing: the next version number will be determined based on commit history. - ``x.y.z``: the next version number will be ``x.y.z``. - ``major|minor|patch``: the next version number will be the current version number with the indicated component bumped. This setting cannot be specified together with ``minMajorVersion``; the invoked script can be used to achieve the effects of ``minMajorVersion``. Default: - The next version will be determined based on the commit history and project settings.
        :param npm_dist_tag: (experimental) The npmDistTag to use when publishing from the default branch. To set the npm dist-tag for release branches, set the ``npmDistTag`` property for each branch. Default: "latest"
        :param post_build_steps: (experimental) Steps to execute after build as part of the release workflow. Default: []
        :param prerelease: (experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre"). Default: - normal semantic versions
        :param publish_dry_run: (experimental) Instead of actually publishing to package managers, just print the publishing command. Default: false
        :param publish_tasks: (experimental) Define publishing tasks that can be executed manually as well as workflows. Normally, publishing only happens within automated workflows. Enable this in order to create a publishing task for each publishing activity. Default: false
        :param releasable_commits: (experimental) Find commits that should be considered releasable Used to decide if a release is required. Default: ReleasableCommits.everyCommit()
        :param release_branches: (experimental) Defines additional release branches. A workflow will be created for each release branch which will publish releases from commits in this branch. Each release branch *must* be assigned a major version number which is used to enforce that versions published from that branch always use that major version. If multiple branches are used, the ``majorVersion`` field must also be provided for the default branch. Default: - no additional branches are used for release. you can use ``addBranch()`` to add additional branches.
        :param release_environment: (experimental) The GitHub Actions environment used for the release. This can be used to add an explicit approval step to the release or limit who can initiate a release through environment protection rules. When multiple artifacts are released, the environment can be overwritten on a per artifact basis. Default: - no environment used, unless set at the artifact level
        :param release_every_commit: (deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``. Default: true
        :param release_failure_issue: (experimental) Create a github issue on every failed publishing task. Default: false
        :param release_failure_issue_label: (experimental) The label to apply to issues indicating publish failures. Only applies if ``releaseFailureIssue`` is true. Default: "failed-release"
        :param release_schedule: (deprecated) CRON schedule to trigger new releases. Default: - no scheduled releases
        :param release_tag_prefix: (experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers. Note: this prefix is used to detect the latest tagged version when bumping, so if you change this on a project with an existing version history, you may need to manually tag your latest release with the new prefix. Default: "v"
        :param release_trigger: (experimental) The release trigger to use. Default: - Continuous releases (``ReleaseTrigger.continuous()``)
        :param release_workflow_env: (experimental) Build environment variables for release workflows. Default: {}
        :param release_workflow_name: (experimental) The name of the default release workflow. Default: "release"
        :param release_workflow_setup_steps: (experimental) A set of workflow steps to execute in order to setup the workflow container.
        :param versionrc_options: (experimental) Custom configuration used when creating changelog with commit-and-tag-version package. Given values either append to default configuration or overwrite values in it. Default: - standard configuration applicable for GitHub repositories
        :param workflow_container_image: (experimental) Container image to use for GitHub workflows. Default: - default image
        :param workflow_runs_on: (experimental) Github Runner selection labels. Default: ["ubuntu-latest"]
        :param workflow_runs_on_group: (experimental) Github Runner Group selection options.
        :param name: (experimental) This is the name of your project. Default: $BASEDIR
        :param commit_generated: (experimental) Whether to commit the managed files by default. Default: true
        :param git_ignore_options: (experimental) Configuration options for .gitignore file.
        :param git_options: (experimental) Configuration options for git.
        :param logging: (experimental) Configure logging options such as verbosity. Default: {}
        :param outdir: (experimental) The root directory of the project. Relative to this directory, all files are synthesized. If this project has a parent, this directory is relative to the parent directory and it cannot be the same as the parent or any of it's other subprojects. Default: "."
        :param parent: (experimental) The parent project, if this project is part of a bigger project.
        :param projen_command: (experimental) The shell command to use in order to run the projen CLI. Can be used to customize in special environments. Default: "npx projen"
        :param projenrc_json: (experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation. Default: false
        :param projenrc_json_options: (experimental) Options for .projenrc.json. Default: - default options
        :param renovatebot: (experimental) Use renovatebot to handle dependency upgrades. Default: false
        :param renovatebot_options: (experimental) Options for renovatebot. Default: - default options

        :stability: experimental
        '''
        options = TypeScriptProjectOptions(
            disable_tsconfig=disable_tsconfig,
            disable_tsconfig_dev=disable_tsconfig_dev,
            docgen=docgen,
            docs_directory=docs_directory,
            entrypoint_types=entrypoint_types,
            eslint=eslint,
            eslint_options=eslint_options,
            libdir=libdir,
            projenrc_ts=projenrc_ts,
            projenrc_ts_options=projenrc_ts_options,
            sample_code=sample_code,
            srcdir=srcdir,
            testdir=testdir,
            tsconfig=tsconfig,
            tsconfig_dev=tsconfig_dev,
            tsconfig_dev_file=tsconfig_dev_file,
            ts_jest_options=ts_jest_options,
            typescript_version=typescript_version,
            default_release_branch=default_release_branch,
            artifacts_directory=artifacts_directory,
            auto_approve_upgrades=auto_approve_upgrades,
            biome=biome,
            biome_options=biome_options,
            build_workflow=build_workflow,
            build_workflow_options=build_workflow_options,
            build_workflow_triggers=build_workflow_triggers,
            bundler_options=bundler_options,
            check_licenses=check_licenses,
            code_cov=code_cov,
            code_cov_token_secret=code_cov_token_secret,
            copyright_owner=copyright_owner,
            copyright_period=copyright_period,
            dependabot=dependabot,
            dependabot_options=dependabot_options,
            deps_upgrade=deps_upgrade,
            deps_upgrade_options=deps_upgrade_options,
            gitignore=gitignore,
            jest=jest,
            jest_options=jest_options,
            mutable_build=mutable_build,
            npmignore=npmignore,
            npmignore_enabled=npmignore_enabled,
            npm_ignore_options=npm_ignore_options,
            package=package,
            prettier=prettier,
            prettier_options=prettier_options,
            projen_dev_dependency=projen_dev_dependency,
            projenrc_js=projenrc_js,
            projenrc_js_options=projenrc_js_options,
            projen_version=projen_version,
            pull_request_template=pull_request_template,
            pull_request_template_contents=pull_request_template_contents,
            release=release,
            release_to_npm=release_to_npm,
            release_workflow=release_workflow,
            workflow_bootstrap_steps=workflow_bootstrap_steps,
            workflow_git_identity=workflow_git_identity,
            workflow_node_version=workflow_node_version,
            workflow_package_cache=workflow_package_cache,
            auto_approve_options=auto_approve_options,
            auto_merge=auto_merge,
            auto_merge_options=auto_merge_options,
            clobber=clobber,
            dev_container=dev_container,
            github=github,
            github_options=github_options,
            gitpod=gitpod,
            mergify=mergify,
            mergify_options=mergify_options,
            project_type=project_type,
            projen_credentials=projen_credentials,
            projen_token_secret=projen_token_secret,
            readme=readme,
            stale=stale,
            stale_options=stale_options,
            vscode=vscode,
            allow_library_dependencies=allow_library_dependencies,
            author_email=author_email,
            author_name=author_name,
            author_organization=author_organization,
            author_url=author_url,
            auto_detect_bin=auto_detect_bin,
            bin=bin,
            bugs_email=bugs_email,
            bugs_url=bugs_url,
            bundled_deps=bundled_deps,
            bun_version=bun_version,
            code_artifact_options=code_artifact_options,
            deps=deps,
            description=description,
            dev_deps=dev_deps,
            entrypoint=entrypoint,
            homepage=homepage,
            keywords=keywords,
            license=license,
            licensed=licensed,
            max_node_version=max_node_version,
            min_node_version=min_node_version,
            npm_access=npm_access,
            npm_provenance=npm_provenance,
            npm_registry=npm_registry,
            npm_registry_url=npm_registry_url,
            npm_token_secret=npm_token_secret,
            npm_trusted_publishing=npm_trusted_publishing,
            package_manager=package_manager,
            package_name=package_name,
            peer_dependency_options=peer_dependency_options,
            peer_deps=peer_deps,
            pnpm_version=pnpm_version,
            repository=repository,
            repository_directory=repository_directory,
            scoped_packages_options=scoped_packages_options,
            scripts=scripts,
            stability=stability,
            yarn_berry_options=yarn_berry_options,
            bump_package=bump_package,
            jsii_release_version=jsii_release_version,
            major_version=major_version,
            min_major_version=min_major_version,
            next_version_command=next_version_command,
            npm_dist_tag=npm_dist_tag,
            post_build_steps=post_build_steps,
            prerelease=prerelease,
            publish_dry_run=publish_dry_run,
            publish_tasks=publish_tasks,
            releasable_commits=releasable_commits,
            release_branches=release_branches,
            release_environment=release_environment,
            release_every_commit=release_every_commit,
            release_failure_issue=release_failure_issue,
            release_failure_issue_label=release_failure_issue_label,
            release_schedule=release_schedule,
            release_tag_prefix=release_tag_prefix,
            release_trigger=release_trigger,
            release_workflow_env=release_workflow_env,
            release_workflow_name=release_workflow_name,
            release_workflow_setup_steps=release_workflow_setup_steps,
            versionrc_options=versionrc_options,
            workflow_container_image=workflow_container_image,
            workflow_runs_on=workflow_runs_on,
            workflow_runs_on_group=workflow_runs_on_group,
            name=name,
            commit_generated=commit_generated,
            git_ignore_options=git_ignore_options,
            git_options=git_options,
            logging=logging,
            outdir=outdir,
            parent=parent,
            projen_command=projen_command,
            projenrc_json=projenrc_json,
            projenrc_json_options=projenrc_json_options,
            renovatebot=renovatebot,
            renovatebot_options=renovatebot_options,
        )

        jsii.create(self.__class__, self, [options])


@jsii.data_type(
    jsii_type="projen.typescript.TypeScriptLibraryProjectOptions",
    jsii_struct_bases=[TypeScriptProjectOptions],
    name_mapping={
        "name": "name",
        "commit_generated": "commitGenerated",
        "git_ignore_options": "gitIgnoreOptions",
        "git_options": "gitOptions",
        "logging": "logging",
        "outdir": "outdir",
        "parent": "parent",
        "projen_command": "projenCommand",
        "projenrc_json": "projenrcJson",
        "projenrc_json_options": "projenrcJsonOptions",
        "renovatebot": "renovatebot",
        "renovatebot_options": "renovatebotOptions",
        "auto_approve_options": "autoApproveOptions",
        "auto_merge": "autoMerge",
        "auto_merge_options": "autoMergeOptions",
        "clobber": "clobber",
        "dev_container": "devContainer",
        "github": "github",
        "github_options": "githubOptions",
        "gitpod": "gitpod",
        "mergify": "mergify",
        "mergify_options": "mergifyOptions",
        "project_type": "projectType",
        "projen_credentials": "projenCredentials",
        "projen_token_secret": "projenTokenSecret",
        "readme": "readme",
        "stale": "stale",
        "stale_options": "staleOptions",
        "vscode": "vscode",
        "allow_library_dependencies": "allowLibraryDependencies",
        "author_email": "authorEmail",
        "author_name": "authorName",
        "author_organization": "authorOrganization",
        "author_url": "authorUrl",
        "auto_detect_bin": "autoDetectBin",
        "bin": "bin",
        "bugs_email": "bugsEmail",
        "bugs_url": "bugsUrl",
        "bundled_deps": "bundledDeps",
        "bun_version": "bunVersion",
        "code_artifact_options": "codeArtifactOptions",
        "deps": "deps",
        "description": "description",
        "dev_deps": "devDeps",
        "entrypoint": "entrypoint",
        "homepage": "homepage",
        "keywords": "keywords",
        "license": "license",
        "licensed": "licensed",
        "max_node_version": "maxNodeVersion",
        "min_node_version": "minNodeVersion",
        "npm_access": "npmAccess",
        "npm_provenance": "npmProvenance",
        "npm_registry": "npmRegistry",
        "npm_registry_url": "npmRegistryUrl",
        "npm_token_secret": "npmTokenSecret",
        "npm_trusted_publishing": "npmTrustedPublishing",
        "package_manager": "packageManager",
        "package_name": "packageName",
        "peer_dependency_options": "peerDependencyOptions",
        "peer_deps": "peerDeps",
        "pnpm_version": "pnpmVersion",
        "repository": "repository",
        "repository_directory": "repositoryDirectory",
        "scoped_packages_options": "scopedPackagesOptions",
        "scripts": "scripts",
        "stability": "stability",
        "yarn_berry_options": "yarnBerryOptions",
        "bump_package": "bumpPackage",
        "jsii_release_version": "jsiiReleaseVersion",
        "major_version": "majorVersion",
        "min_major_version": "minMajorVersion",
        "next_version_command": "nextVersionCommand",
        "npm_dist_tag": "npmDistTag",
        "post_build_steps": "postBuildSteps",
        "prerelease": "prerelease",
        "publish_dry_run": "publishDryRun",
        "publish_tasks": "publishTasks",
        "releasable_commits": "releasableCommits",
        "release_branches": "releaseBranches",
        "release_environment": "releaseEnvironment",
        "release_every_commit": "releaseEveryCommit",
        "release_failure_issue": "releaseFailureIssue",
        "release_failure_issue_label": "releaseFailureIssueLabel",
        "release_schedule": "releaseSchedule",
        "release_tag_prefix": "releaseTagPrefix",
        "release_trigger": "releaseTrigger",
        "release_workflow_env": "releaseWorkflowEnv",
        "release_workflow_name": "releaseWorkflowName",
        "release_workflow_setup_steps": "releaseWorkflowSetupSteps",
        "versionrc_options": "versionrcOptions",
        "workflow_container_image": "workflowContainerImage",
        "workflow_runs_on": "workflowRunsOn",
        "workflow_runs_on_group": "workflowRunsOnGroup",
        "default_release_branch": "defaultReleaseBranch",
        "artifacts_directory": "artifactsDirectory",
        "auto_approve_upgrades": "autoApproveUpgrades",
        "biome": "biome",
        "biome_options": "biomeOptions",
        "build_workflow": "buildWorkflow",
        "build_workflow_options": "buildWorkflowOptions",
        "build_workflow_triggers": "buildWorkflowTriggers",
        "bundler_options": "bundlerOptions",
        "check_licenses": "checkLicenses",
        "code_cov": "codeCov",
        "code_cov_token_secret": "codeCovTokenSecret",
        "copyright_owner": "copyrightOwner",
        "copyright_period": "copyrightPeriod",
        "dependabot": "dependabot",
        "dependabot_options": "dependabotOptions",
        "deps_upgrade": "depsUpgrade",
        "deps_upgrade_options": "depsUpgradeOptions",
        "gitignore": "gitignore",
        "jest": "jest",
        "jest_options": "jestOptions",
        "mutable_build": "mutableBuild",
        "npmignore": "npmignore",
        "npmignore_enabled": "npmignoreEnabled",
        "npm_ignore_options": "npmIgnoreOptions",
        "package": "package",
        "prettier": "prettier",
        "prettier_options": "prettierOptions",
        "projen_dev_dependency": "projenDevDependency",
        "projenrc_js": "projenrcJs",
        "projenrc_js_options": "projenrcJsOptions",
        "projen_version": "projenVersion",
        "pull_request_template": "pullRequestTemplate",
        "pull_request_template_contents": "pullRequestTemplateContents",
        "release": "release",
        "release_to_npm": "releaseToNpm",
        "release_workflow": "releaseWorkflow",
        "workflow_bootstrap_steps": "workflowBootstrapSteps",
        "workflow_git_identity": "workflowGitIdentity",
        "workflow_node_version": "workflowNodeVersion",
        "workflow_package_cache": "workflowPackageCache",
        "disable_tsconfig": "disableTsconfig",
        "disable_tsconfig_dev": "disableTsconfigDev",
        "docgen": "docgen",
        "docs_directory": "docsDirectory",
        "entrypoint_types": "entrypointTypes",
        "eslint": "eslint",
        "eslint_options": "eslintOptions",
        "libdir": "libdir",
        "projenrc_ts": "projenrcTs",
        "projenrc_ts_options": "projenrcTsOptions",
        "sample_code": "sampleCode",
        "srcdir": "srcdir",
        "testdir": "testdir",
        "tsconfig": "tsconfig",
        "tsconfig_dev": "tsconfigDev",
        "tsconfig_dev_file": "tsconfigDevFile",
        "ts_jest_options": "tsJestOptions",
        "typescript_version": "typescriptVersion",
    },
)
class TypeScriptLibraryProjectOptions(TypeScriptProjectOptions):
    def __init__(
        self,
        *,
        name: builtins.str,
        commit_generated: typing.Optional[builtins.bool] = None,
        git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
        logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
        outdir: typing.Optional[builtins.str] = None,
        parent: typing.Optional[_Project_57d89203] = None,
        projen_command: typing.Optional[builtins.str] = None,
        projenrc_json: typing.Optional[builtins.bool] = None,
        projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
        renovatebot: typing.Optional[builtins.bool] = None,
        renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_merge: typing.Optional[builtins.bool] = None,
        auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
        clobber: typing.Optional[builtins.bool] = None,
        dev_container: typing.Optional[builtins.bool] = None,
        github: typing.Optional[builtins.bool] = None,
        github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
        gitpod: typing.Optional[builtins.bool] = None,
        mergify: typing.Optional[builtins.bool] = None,
        mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
        project_type: typing.Optional[_ProjectType_fd80c725] = None,
        projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
        projen_token_secret: typing.Optional[builtins.str] = None,
        readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
        stale: typing.Optional[builtins.bool] = None,
        stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
        vscode: typing.Optional[builtins.bool] = None,
        allow_library_dependencies: typing.Optional[builtins.bool] = None,
        author_email: typing.Optional[builtins.str] = None,
        author_name: typing.Optional[builtins.str] = None,
        author_organization: typing.Optional[builtins.bool] = None,
        author_url: typing.Optional[builtins.str] = None,
        auto_detect_bin: typing.Optional[builtins.bool] = None,
        bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        bugs_email: typing.Optional[builtins.str] = None,
        bugs_url: typing.Optional[builtins.str] = None,
        bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        bun_version: typing.Optional[builtins.str] = None,
        code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
        deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        entrypoint: typing.Optional[builtins.str] = None,
        homepage: typing.Optional[builtins.str] = None,
        keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
        license: typing.Optional[builtins.str] = None,
        licensed: typing.Optional[builtins.bool] = None,
        max_node_version: typing.Optional[builtins.str] = None,
        min_node_version: typing.Optional[builtins.str] = None,
        npm_access: typing.Optional[_NpmAccess_134fa228] = None,
        npm_provenance: typing.Optional[builtins.bool] = None,
        npm_registry: typing.Optional[builtins.str] = None,
        npm_registry_url: typing.Optional[builtins.str] = None,
        npm_token_secret: typing.Optional[builtins.str] = None,
        npm_trusted_publishing: typing.Optional[builtins.bool] = None,
        package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
        package_name: typing.Optional[builtins.str] = None,
        peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
        peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
        pnpm_version: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        repository_directory: typing.Optional[builtins.str] = None,
        scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
        scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        stability: typing.Optional[builtins.str] = None,
        yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
        bump_package: typing.Optional[builtins.str] = None,
        jsii_release_version: typing.Optional[builtins.str] = None,
        major_version: typing.Optional[jsii.Number] = None,
        min_major_version: typing.Optional[jsii.Number] = None,
        next_version_command: typing.Optional[builtins.str] = None,
        npm_dist_tag: typing.Optional[builtins.str] = None,
        post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        prerelease: typing.Optional[builtins.str] = None,
        publish_dry_run: typing.Optional[builtins.bool] = None,
        publish_tasks: typing.Optional[builtins.bool] = None,
        releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
        release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
        release_environment: typing.Optional[builtins.str] = None,
        release_every_commit: typing.Optional[builtins.bool] = None,
        release_failure_issue: typing.Optional[builtins.bool] = None,
        release_failure_issue_label: typing.Optional[builtins.str] = None,
        release_schedule: typing.Optional[builtins.str] = None,
        release_tag_prefix: typing.Optional[builtins.str] = None,
        release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
        release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        release_workflow_name: typing.Optional[builtins.str] = None,
        release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        workflow_container_image: typing.Optional[builtins.str] = None,
        workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
        workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
        default_release_branch: builtins.str,
        artifacts_directory: typing.Optional[builtins.str] = None,
        auto_approve_upgrades: typing.Optional[builtins.bool] = None,
        biome: typing.Optional[builtins.bool] = None,
        biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow: typing.Optional[builtins.bool] = None,
        build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
        build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
        bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
        check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
        code_cov: typing.Optional[builtins.bool] = None,
        code_cov_token_secret: typing.Optional[builtins.str] = None,
        copyright_owner: typing.Optional[builtins.str] = None,
        copyright_period: typing.Optional[builtins.str] = None,
        dependabot: typing.Optional[builtins.bool] = None,
        dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
        deps_upgrade: typing.Optional[builtins.bool] = None,
        deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
        gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        jest: typing.Optional[builtins.bool] = None,
        jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
        mutable_build: typing.Optional[builtins.bool] = None,
        npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
        npmignore_enabled: typing.Optional[builtins.bool] = None,
        npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
        package: typing.Optional[builtins.bool] = None,
        prettier: typing.Optional[builtins.bool] = None,
        prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_dev_dependency: typing.Optional[builtins.bool] = None,
        projenrc_js: typing.Optional[builtins.bool] = None,
        projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
        projen_version: typing.Optional[builtins.str] = None,
        pull_request_template: typing.Optional[builtins.bool] = None,
        pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
        release: typing.Optional[builtins.bool] = None,
        release_to_npm: typing.Optional[builtins.bool] = None,
        release_workflow: typing.Optional[builtins.bool] = None,
        workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
        workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
        workflow_node_version: typing.Optional[builtins.str] = None,
        workflow_package_cache: typing.Optional[builtins.bool] = None,
        disable_tsconfig: typing.Optional[builtins.bool] = None,
        disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
        docgen: typing.Optional[builtins.bool] = None,
        docs_directory: typing.Optional[builtins.str] = None,
        entrypoint_types: typing.Optional[builtins.str] = None,
        eslint: typing.Optional[builtins.bool] = None,
        eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
        libdir: typing.Optional[builtins.str] = None,
        projenrc_ts: typing.Optional[builtins.bool] = None,
        projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        sample_code: typing.Optional[builtins.bool] = None,
        srcdir: typing.Optional[builtins.str] = None,
        testdir: typing.Optional[builtins.str] = None,
        tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
        tsconfig_dev_file: typing.Optional[builtins.str] = None,
        ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        typescript_version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param name: (experimental) This is the name of your project. Default: $BASEDIR
        :param commit_generated: (experimental) Whether to commit the managed files by default. Default: true
        :param git_ignore_options: (experimental) Configuration options for .gitignore file.
        :param git_options: (experimental) Configuration options for git.
        :param logging: (experimental) Configure logging options such as verbosity. Default: {}
        :param outdir: (experimental) The root directory of the project. Relative to this directory, all files are synthesized. If this project has a parent, this directory is relative to the parent directory and it cannot be the same as the parent or any of it's other subprojects. Default: "."
        :param parent: (experimental) The parent project, if this project is part of a bigger project.
        :param projen_command: (experimental) The shell command to use in order to run the projen CLI. Can be used to customize in special environments. Default: "npx projen"
        :param projenrc_json: (experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation. Default: false
        :param projenrc_json_options: (experimental) Options for .projenrc.json. Default: - default options
        :param renovatebot: (experimental) Use renovatebot to handle dependency upgrades. Default: false
        :param renovatebot_options: (experimental) Options for renovatebot. Default: - default options
        :param auto_approve_options: (experimental) Enable and configure the 'auto approve' workflow. Default: - auto approve is disabled
        :param auto_merge: (experimental) Enable automatic merging on GitHub. Has no effect if ``github.mergify`` is set to false. Default: true
        :param auto_merge_options: (experimental) Configure options for automatic merging on GitHub. Has no effect if ``github.mergify`` or ``autoMerge`` is set to false. Default: - see defaults in ``AutoMergeOptions``
        :param clobber: (experimental) Add a ``clobber`` task which resets the repo to origin. Default: - true, but false for subprojects
        :param dev_container: (experimental) Add a VSCode development environment (used for GitHub Codespaces). Default: false
        :param github: (experimental) Enable GitHub integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param github_options: (experimental) Options for GitHub integration. Default: - see GitHubOptions
        :param gitpod: (experimental) Add a Gitpod development environment. Default: false
        :param mergify: (deprecated) Whether mergify should be enabled on this repository or not. Default: true
        :param mergify_options: (deprecated) Options for mergify. Default: - default options
        :param project_type: (deprecated) Which type of project this is (library/app). Default: ProjectType.UNKNOWN
        :param projen_credentials: (experimental) Choose a method of providing GitHub API access for projen workflows. Default: - use a personal access token named PROJEN_GITHUB_TOKEN
        :param projen_token_secret: (deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows. This token needs to have the ``repo``, ``workflows`` and ``packages`` scope. Default: "PROJEN_GITHUB_TOKEN"
        :param readme: (experimental) The README setup. Default: - { filename: 'README.md', contents: '# replace this' }
        :param stale: (experimental) Auto-close of stale issues and pull request. See ``staleOptions`` for options. Default: false
        :param stale_options: (experimental) Auto-close stale issues and pull requests. To disable set ``stale`` to ``false``. Default: - see defaults in ``StaleOptions``
        :param vscode: (experimental) Enable VSCode integration. Enabled by default for root projects. Disabled for non-root projects. Default: true
        :param allow_library_dependencies: (experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``. This is normally only allowed for libraries. For apps, there's no meaning for specifying these. Default: true
        :param author_email: (experimental) Author's e-mail.
        :param author_name: (experimental) Author's name.
        :param author_organization: (experimental) Is the author an organization.
        :param author_url: (experimental) Author's URL / Website.
        :param auto_detect_bin: (experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section. Default: true
        :param bin: (experimental) Binary programs vended with your module. You can use this option to add/customize how binaries are represented in your ``package.json``, but unless ``autoDetectBin`` is ``false``, every executable file under ``bin`` will automatically be added to this section.
        :param bugs_email: (experimental) The email address to which issues should be reported.
        :param bugs_url: (experimental) The url to your project's issue tracker.
        :param bundled_deps: (experimental) List of dependencies to bundle into this module. These modules will be added both to the ``dependencies`` section and ``bundledDependencies`` section of your ``package.json``. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include.
        :param bun_version: (experimental) The version of Bun to use if using Bun as a package manager. Default: "latest"
        :param code_artifact_options: (experimental) Options for npm packages using AWS CodeArtifact. This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact Default: - undefined
        :param deps: (experimental) Runtime dependencies of this module. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param description: (experimental) The description is just a string that helps people understand the purpose of the package. It can be used when searching for packages in a package manager as well. See https://classic.yarnpkg.com/en/docs/package-json/#toc-description
        :param dev_deps: (experimental) Build dependencies for this module. These dependencies will only be available in your build environment but will not be fetched when this module is consumed. The recommendation is to only specify the module name here (e.g. ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the sense that it will add the module as a dependency to your ``package.json`` file with the latest version (``^``). You can specify semver requirements in the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and this will be what you ``package.json`` will eventually include. Default: []
        :param entrypoint: (experimental) Module entrypoint (``main`` in ``package.json``). Set to an empty string to not include ``main`` in your package.json Default: "lib/index.js"
        :param homepage: (experimental) Package's Homepage / Website.
        :param keywords: (experimental) Keywords to include in ``package.json``.
        :param license: (experimental) License's SPDX identifier. See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses. Use the ``licensed`` option if you want to no license to be specified. Default: "Apache-2.0"
        :param licensed: (experimental) Indicates if a license should be added. Default: true
        :param max_node_version: (experimental) The maximum node version supported by this package. Most projects should not use this option. The value indicates that the package is incompatible with any newer versions of node. This requirement is enforced via the engines field. You will normally not need to set this option. Consider this option only if your package is known to not function with newer versions of node. Default: - no maximum version is enforced
        :param min_node_version: (experimental) The minimum node version required by this package to function. Most projects should not use this option. The value indicates that the package is incompatible with any older versions of node. This requirement is enforced via the engines field. You will normally not need to set this option, even if your package is incompatible with EOL versions of node. Consider this option only if your package depends on a specific feature, that is not available in other LTS versions. Setting this option has very high impact on the consumers of your package, as package managers will actively prevent usage with node versions you have marked as incompatible. To change the node version of your CI/CD workflows, use ``workflowNodeVersion``. Default: - no minimum version is enforced
        :param npm_access: (experimental) Access level of the npm package. Default: - for scoped packages (e.g. ``foo@bar``), the default is ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is ``NpmAccess.PUBLIC``.
        :param npm_provenance: (experimental) Should provenance statements be generated when the package is published. A supported package manager is required to publish a package with npm provenance statements and you will need to use a supported CI/CD provider. Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages, which is using npm internally and supports provenance statements independently of the package manager used. Default: - true for public packages, false otherwise
        :param npm_registry: (deprecated) The host name of the npm registry to publish to. Cannot be set together with ``npmRegistryUrl``.
        :param npm_registry_url: (experimental) The base URL of the npm package registry. Must be a URL (e.g. start with "https://" or "http://") Default: "https://registry.npmjs.org"
        :param npm_token_secret: (experimental) GitHub secret which contains the NPM token to use when publishing packages. Default: "NPM_TOKEN"
        :param npm_trusted_publishing: (experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work. Default: - false
        :param package_manager: (experimental) The Node Package Manager used to execute scripts. Default: NodePackageManager.YARN_CLASSIC
        :param package_name: (experimental) The "name" in package.json. Default: - defaults to project name
        :param peer_dependency_options: (experimental) Options for ``peerDeps``.
        :param peer_deps: (experimental) Peer dependencies for this module. Dependencies listed here are required to be installed (and satisfied) by the *consumer* of this library. Using peer dependencies allows you to ensure that only a single module of a certain library exists in the ``node_modules`` tree of your consumers. Note that prior to npm@7, peer dependencies are *not* automatically installed, which means that adding peer dependencies to a library will be a breaking change for your customers. Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is enabled by default), projen will automatically add a dev dependency with a pinned version for each peer dependency. This will ensure that you build & test your module against the lowest peer version required. Default: []
        :param pnpm_version: (experimental) The version of PNPM to use if using PNPM as a package manager. Default: "9"
        :param repository: (experimental) The repository is the location where the actual code for your package lives. See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository
        :param repository_directory: (experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.
        :param scoped_packages_options: (experimental) Options for privately hosted scoped packages. Default: - fetch all scoped packages from the public npm registry
        :param scripts: (deprecated) npm scripts to include. If a script has the same name as a standard script, the standard script will be overwritten. Also adds the script as a task. Default: {}
        :param stability: (experimental) Package's Stability.
        :param yarn_berry_options: (experimental) Options for Yarn Berry. Default: - Yarn Berry v4 with all default options
        :param bump_package: (experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string. This can be any compatible package version, including the deprecated ``standard-version@9``. Default: - A recent version of "commit-and-tag-version"
        :param jsii_release_version: (experimental) Version requirement of ``publib`` which is used to publish modules to npm. Default: "latest"
        :param major_version: (experimental) Major version to release from the default branch. If this is specified, we bump the latest version of this major version line. If not specified, we bump the global latest version. Default: - Major version is not enforced.
        :param min_major_version: (experimental) Minimal Major version to release. This can be useful to set to 1, as breaking changes before the 1.x major release are not incrementing the major version number. Can not be set together with ``majorVersion``. Default: - No minimum version is being enforced
        :param next_version_command: (experimental) A shell command to control the next version to release. If present, this shell command will be run before the bump is executed, and it determines what version to release. It will be executed in the following environment: - Working directory: the project directory. - ``$VERSION``: the current version. Looks like ``1.2.3``. - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset. - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``. The command should print one of the following to ``stdout``: - Nothing: the next version number will be determined based on commit history. - ``x.y.z``: the next version number will be ``x.y.z``. - ``major|minor|patch``: the next version number will be the current version number with the indicated component bumped. This setting cannot be specified together with ``minMajorVersion``; the invoked script can be used to achieve the effects of ``minMajorVersion``. Default: - The next version will be determined based on the commit history and project settings.
        :param npm_dist_tag: (experimental) The npmDistTag to use when publishing from the default branch. To set the npm dist-tag for release branches, set the ``npmDistTag`` property for each branch. Default: "latest"
        :param post_build_steps: (experimental) Steps to execute after build as part of the release workflow. Default: []
        :param prerelease: (experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre"). Default: - normal semantic versions
        :param publish_dry_run: (experimental) Instead of actually publishing to package managers, just print the publishing command. Default: false
        :param publish_tasks: (experimental) Define publishing tasks that can be executed manually as well as workflows. Normally, publishing only happens within automated workflows. Enable this in order to create a publishing task for each publishing activity. Default: false
        :param releasable_commits: (experimental) Find commits that should be considered releasable Used to decide if a release is required. Default: ReleasableCommits.everyCommit()
        :param release_branches: (experimental) Defines additional release branches. A workflow will be created for each release branch which will publish releases from commits in this branch. Each release branch *must* be assigned a major version number which is used to enforce that versions published from that branch always use that major version. If multiple branches are used, the ``majorVersion`` field must also be provided for the default branch. Default: - no additional branches are used for release. you can use ``addBranch()`` to add additional branches.
        :param release_environment: (experimental) The GitHub Actions environment used for the release. This can be used to add an explicit approval step to the release or limit who can initiate a release through environment protection rules. When multiple artifacts are released, the environment can be overwritten on a per artifact basis. Default: - no environment used, unless set at the artifact level
        :param release_every_commit: (deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``. Default: true
        :param release_failure_issue: (experimental) Create a github issue on every failed publishing task. Default: false
        :param release_failure_issue_label: (experimental) The label to apply to issues indicating publish failures. Only applies if ``releaseFailureIssue`` is true. Default: "failed-release"
        :param release_schedule: (deprecated) CRON schedule to trigger new releases. Default: - no scheduled releases
        :param release_tag_prefix: (experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers. Note: this prefix is used to detect the latest tagged version when bumping, so if you change this on a project with an existing version history, you may need to manually tag your latest release with the new prefix. Default: "v"
        :param release_trigger: (experimental) The release trigger to use. Default: - Continuous releases (``ReleaseTrigger.continuous()``)
        :param release_workflow_env: (experimental) Build environment variables for release workflows. Default: {}
        :param release_workflow_name: (experimental) The name of the default release workflow. Default: "release"
        :param release_workflow_setup_steps: (experimental) A set of workflow steps to execute in order to setup the workflow container.
        :param versionrc_options: (experimental) Custom configuration used when creating changelog with commit-and-tag-version package. Given values either append to default configuration or overwrite values in it. Default: - standard configuration applicable for GitHub repositories
        :param workflow_container_image: (experimental) Container image to use for GitHub workflows. Default: - default image
        :param workflow_runs_on: (experimental) Github Runner selection labels. Default: ["ubuntu-latest"]
        :param workflow_runs_on_group: (experimental) Github Runner Group selection options.
        :param default_release_branch: (experimental) The name of the main release branch. Default: "main"
        :param artifacts_directory: (experimental) A directory which will contain build artifacts. Default: "dist"
        :param auto_approve_upgrades: (experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued). Throw if set to true but ``autoApproveOptions`` are not defined. Default: - true
        :param biome: (experimental) Setup Biome. Default: false
        :param biome_options: (experimental) Biome options. Default: - default options
        :param build_workflow: (experimental) Define a GitHub workflow for building PRs. Default: - true if not a subproject
        :param build_workflow_options: (experimental) Options for PR build workflow.
        :param build_workflow_triggers: (deprecated) Build workflow triggers. Default: "{ pullRequest: {}, workflowDispatch: {} }"
        :param bundler_options: (experimental) Options for ``Bundler``.
        :param check_licenses: (experimental) Configure which licenses should be deemed acceptable for use by dependencies. This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered. Default: - no license checks are run during the build and all licenses will be accepted
        :param code_cov: (experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``. Default: false
        :param code_cov_token_secret: (experimental) Define the secret name for a specified https://codecov.io/ token. Default: - OIDC auth is used
        :param copyright_owner: (experimental) License copyright owner. Default: - defaults to the value of authorName or "" if ``authorName`` is undefined.
        :param copyright_period: (experimental) The copyright years to put in the LICENSE file. Default: - current year
        :param dependabot: (experimental) Use dependabot to handle dependency upgrades. Cannot be used in conjunction with ``depsUpgrade``. Default: false
        :param dependabot_options: (experimental) Options for dependabot. Default: - default options
        :param deps_upgrade: (experimental) Use tasks and github workflows to handle dependency upgrades. Cannot be used in conjunction with ``dependabot``. Default: true
        :param deps_upgrade_options: (experimental) Options for ``UpgradeDependencies``. Default: - default options
        :param gitignore: (experimental) Additional entries to .gitignore.
        :param jest: (experimental) Setup jest unit tests. Default: true
        :param jest_options: (experimental) Jest options. Default: - default options
        :param mutable_build: (deprecated) Automatically update files modified during builds to pull-request branches. This means that any files synthesized by projen or e.g. test snapshots will always be up-to-date before a PR is merged. Implies that PR builds do not have anti-tamper checks. Default: true
        :param npmignore: (deprecated) Additional entries to .npmignore.
        :param npmignore_enabled: (experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs. Default: true
        :param npm_ignore_options: (experimental) Configuration options for .npmignore file.
        :param package: (experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``). Default: true
        :param prettier: (experimental) Setup prettier. Default: false
        :param prettier_options: (experimental) Prettier options. Default: - default options
        :param projen_dev_dependency: (experimental) Indicates of "projen" should be installed as a devDependency. Default: - true if not a subproject
        :param projenrc_js: (experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation. Default: - true if projenrcJson is false
        :param projenrc_js_options: (experimental) Options for .projenrc.js. Default: - default options
        :param projen_version: (experimental) Version of projen to install. Default: - Defaults to the latest version.
        :param pull_request_template: (experimental) Include a GitHub pull request template. Default: true
        :param pull_request_template_contents: (experimental) The contents of the pull request template. Default: - default content
        :param release: (experimental) Add release management to this project. Default: - true (false for subprojects)
        :param release_to_npm: (experimental) Automatically release to npm when new versions are introduced. Default: false
        :param release_workflow: (deprecated) DEPRECATED: renamed to ``release``. Default: - true if not a subproject
        :param workflow_bootstrap_steps: (experimental) Workflow steps to use in order to bootstrap this repo. Default: "yarn install --frozen-lockfile && yarn projen"
        :param workflow_git_identity: (experimental) The git identity to use in workflows. Default: - default GitHub Actions user
        :param workflow_node_version: (experimental) The node version used in GitHub Actions workflows. Always use this option if your GitHub Actions workflows require a specific to run. Default: - ``minNodeVersion`` if set, otherwise ``lts/*``.
        :param workflow_package_cache: (experimental) Enable Node.js package cache in GitHub workflows. Default: false
        :param disable_tsconfig: (experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler). Default: false
        :param disable_tsconfig_dev: (experimental) Do not generate a ``tsconfig.dev.json`` file. Default: false
        :param docgen: (experimental) Docgen by Typedoc. Default: false
        :param docs_directory: (experimental) Docs directory. Default: "docs"
        :param entrypoint_types: (experimental) The .d.ts file that includes the type declarations for this module. Default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)
        :param eslint: (experimental) Setup eslint. Default: - true, unless biome is enabled
        :param eslint_options: (experimental) Eslint options. Default: - opinionated default options
        :param libdir: (experimental) Typescript artifacts output directory. Default: "lib"
        :param projenrc_ts: (experimental) Use TypeScript for your projenrc file (``.projenrc.ts``). Default: false
        :param projenrc_ts_options: (experimental) Options for .projenrc.ts.
        :param sample_code: (experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there. Default: true
        :param srcdir: (experimental) Typescript sources directory. Default: "src"
        :param testdir: (experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``. If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``), then tests are going to be compiled into ``lib/`` and executed as javascript. If the test directory is outside of ``src``, then we configure jest to compile the code in-memory. Default: "test"
        :param tsconfig: (experimental) Custom TSConfig. Default: - default options
        :param tsconfig_dev: (experimental) Custom tsconfig options for the development tsconfig.json file (used for testing). Default: - use the production tsconfig options
        :param tsconfig_dev_file: (experimental) The name of the development tsconfig.json file. Default: "tsconfig.dev.json"
        :param ts_jest_options: (experimental) Options for ts-jest.
        :param typescript_version: (experimental) TypeScript version to use. NOTE: Typescript is not semantically versioned and should remain on the same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``). Default: "latest"

        :deprecated: use TypeScriptProjectOptions

        :stability: deprecated
        '''
        if isinstance(git_ignore_options, dict):
            git_ignore_options = _IgnoreFileOptions_86c48b91(**git_ignore_options)
        if isinstance(git_options, dict):
            git_options = _GitOptions_a65916a3(**git_options)
        if isinstance(logging, dict):
            logging = _LoggerOptions_eb0f6309(**logging)
        if isinstance(projenrc_json_options, dict):
            projenrc_json_options = _ProjenrcJsonOptions_9c40dd4f(**projenrc_json_options)
        if isinstance(renovatebot_options, dict):
            renovatebot_options = _RenovatebotOptions_18e6b8a1(**renovatebot_options)
        if isinstance(auto_approve_options, dict):
            auto_approve_options = _AutoApproveOptions_dac86cbe(**auto_approve_options)
        if isinstance(auto_merge_options, dict):
            auto_merge_options = _AutoMergeOptions_d112cd3c(**auto_merge_options)
        if isinstance(github_options, dict):
            github_options = _GitHubOptions_21553699(**github_options)
        if isinstance(mergify_options, dict):
            mergify_options = _MergifyOptions_a6faaab3(**mergify_options)
        if isinstance(readme, dict):
            readme = _SampleReadmeProps_3518b03b(**readme)
        if isinstance(stale_options, dict):
            stale_options = _StaleOptions_929db764(**stale_options)
        if isinstance(code_artifact_options, dict):
            code_artifact_options = _CodeArtifactOptions_e4782b3e(**code_artifact_options)
        if isinstance(peer_dependency_options, dict):
            peer_dependency_options = _PeerDependencyOptions_99d7d493(**peer_dependency_options)
        if isinstance(yarn_berry_options, dict):
            yarn_berry_options = _YarnBerryOptions_b6942539(**yarn_berry_options)
        if isinstance(workflow_runs_on_group, dict):
            workflow_runs_on_group = _GroupRunnerOptions_148c59c1(**workflow_runs_on_group)
        if isinstance(biome_options, dict):
            biome_options = _BiomeOptions_452ab984(**biome_options)
        if isinstance(build_workflow_options, dict):
            build_workflow_options = _BuildWorkflowOptions_b756f97f(**build_workflow_options)
        if isinstance(build_workflow_triggers, dict):
            build_workflow_triggers = _Triggers_e9ae7617(**build_workflow_triggers)
        if isinstance(bundler_options, dict):
            bundler_options = _BundlerOptions_d60b85ed(**bundler_options)
        if isinstance(check_licenses, dict):
            check_licenses = _LicenseCheckerOptions_80bcd362(**check_licenses)
        if isinstance(dependabot_options, dict):
            dependabot_options = _DependabotOptions_0cedc635(**dependabot_options)
        if isinstance(deps_upgrade_options, dict):
            deps_upgrade_options = _UpgradeDependenciesOptions_1d8ce4da(**deps_upgrade_options)
        if isinstance(jest_options, dict):
            jest_options = _JestOptions_a085f64e(**jest_options)
        if isinstance(npm_ignore_options, dict):
            npm_ignore_options = _IgnoreFileOptions_86c48b91(**npm_ignore_options)
        if isinstance(prettier_options, dict):
            prettier_options = _PrettierOptions_41a5f203(**prettier_options)
        if isinstance(projenrc_js_options, dict):
            projenrc_js_options = _ProjenrcOptions_179dd39f(**projenrc_js_options)
        if isinstance(workflow_git_identity, dict):
            workflow_git_identity = _GitIdentity_6effc3de(**workflow_git_identity)
        if isinstance(eslint_options, dict):
            eslint_options = _EslintOptions_824f60bb(**eslint_options)
        if isinstance(projenrc_ts_options, dict):
            projenrc_ts_options = ProjenrcOptions(**projenrc_ts_options)
        if isinstance(tsconfig, dict):
            tsconfig = _TypescriptConfigOptions_8c5492cd(**tsconfig)
        if isinstance(tsconfig_dev, dict):
            tsconfig_dev = _TypescriptConfigOptions_8c5492cd(**tsconfig_dev)
        if isinstance(ts_jest_options, dict):
            ts_jest_options = TsJestOptions(**ts_jest_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ac162883b4ecfe9863890d69bffa76d7f9ce16e619c94b9b2a4b7b8f222c3227)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument commit_generated", value=commit_generated, expected_type=type_hints["commit_generated"])
            check_type(argname="argument git_ignore_options", value=git_ignore_options, expected_type=type_hints["git_ignore_options"])
            check_type(argname="argument git_options", value=git_options, expected_type=type_hints["git_options"])
            check_type(argname="argument logging", value=logging, expected_type=type_hints["logging"])
            check_type(argname="argument outdir", value=outdir, expected_type=type_hints["outdir"])
            check_type(argname="argument parent", value=parent, expected_type=type_hints["parent"])
            check_type(argname="argument projen_command", value=projen_command, expected_type=type_hints["projen_command"])
            check_type(argname="argument projenrc_json", value=projenrc_json, expected_type=type_hints["projenrc_json"])
            check_type(argname="argument projenrc_json_options", value=projenrc_json_options, expected_type=type_hints["projenrc_json_options"])
            check_type(argname="argument renovatebot", value=renovatebot, expected_type=type_hints["renovatebot"])
            check_type(argname="argument renovatebot_options", value=renovatebot_options, expected_type=type_hints["renovatebot_options"])
            check_type(argname="argument auto_approve_options", value=auto_approve_options, expected_type=type_hints["auto_approve_options"])
            check_type(argname="argument auto_merge", value=auto_merge, expected_type=type_hints["auto_merge"])
            check_type(argname="argument auto_merge_options", value=auto_merge_options, expected_type=type_hints["auto_merge_options"])
            check_type(argname="argument clobber", value=clobber, expected_type=type_hints["clobber"])
            check_type(argname="argument dev_container", value=dev_container, expected_type=type_hints["dev_container"])
            check_type(argname="argument github", value=github, expected_type=type_hints["github"])
            check_type(argname="argument github_options", value=github_options, expected_type=type_hints["github_options"])
            check_type(argname="argument gitpod", value=gitpod, expected_type=type_hints["gitpod"])
            check_type(argname="argument mergify", value=mergify, expected_type=type_hints["mergify"])
            check_type(argname="argument mergify_options", value=mergify_options, expected_type=type_hints["mergify_options"])
            check_type(argname="argument project_type", value=project_type, expected_type=type_hints["project_type"])
            check_type(argname="argument projen_credentials", value=projen_credentials, expected_type=type_hints["projen_credentials"])
            check_type(argname="argument projen_token_secret", value=projen_token_secret, expected_type=type_hints["projen_token_secret"])
            check_type(argname="argument readme", value=readme, expected_type=type_hints["readme"])
            check_type(argname="argument stale", value=stale, expected_type=type_hints["stale"])
            check_type(argname="argument stale_options", value=stale_options, expected_type=type_hints["stale_options"])
            check_type(argname="argument vscode", value=vscode, expected_type=type_hints["vscode"])
            check_type(argname="argument allow_library_dependencies", value=allow_library_dependencies, expected_type=type_hints["allow_library_dependencies"])
            check_type(argname="argument author_email", value=author_email, expected_type=type_hints["author_email"])
            check_type(argname="argument author_name", value=author_name, expected_type=type_hints["author_name"])
            check_type(argname="argument author_organization", value=author_organization, expected_type=type_hints["author_organization"])
            check_type(argname="argument author_url", value=author_url, expected_type=type_hints["author_url"])
            check_type(argname="argument auto_detect_bin", value=auto_detect_bin, expected_type=type_hints["auto_detect_bin"])
            check_type(argname="argument bin", value=bin, expected_type=type_hints["bin"])
            check_type(argname="argument bugs_email", value=bugs_email, expected_type=type_hints["bugs_email"])
            check_type(argname="argument bugs_url", value=bugs_url, expected_type=type_hints["bugs_url"])
            check_type(argname="argument bundled_deps", value=bundled_deps, expected_type=type_hints["bundled_deps"])
            check_type(argname="argument bun_version", value=bun_version, expected_type=type_hints["bun_version"])
            check_type(argname="argument code_artifact_options", value=code_artifact_options, expected_type=type_hints["code_artifact_options"])
            check_type(argname="argument deps", value=deps, expected_type=type_hints["deps"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument dev_deps", value=dev_deps, expected_type=type_hints["dev_deps"])
            check_type(argname="argument entrypoint", value=entrypoint, expected_type=type_hints["entrypoint"])
            check_type(argname="argument homepage", value=homepage, expected_type=type_hints["homepage"])
            check_type(argname="argument keywords", value=keywords, expected_type=type_hints["keywords"])
            check_type(argname="argument license", value=license, expected_type=type_hints["license"])
            check_type(argname="argument licensed", value=licensed, expected_type=type_hints["licensed"])
            check_type(argname="argument max_node_version", value=max_node_version, expected_type=type_hints["max_node_version"])
            check_type(argname="argument min_node_version", value=min_node_version, expected_type=type_hints["min_node_version"])
            check_type(argname="argument npm_access", value=npm_access, expected_type=type_hints["npm_access"])
            check_type(argname="argument npm_provenance", value=npm_provenance, expected_type=type_hints["npm_provenance"])
            check_type(argname="argument npm_registry", value=npm_registry, expected_type=type_hints["npm_registry"])
            check_type(argname="argument npm_registry_url", value=npm_registry_url, expected_type=type_hints["npm_registry_url"])
            check_type(argname="argument npm_token_secret", value=npm_token_secret, expected_type=type_hints["npm_token_secret"])
            check_type(argname="argument npm_trusted_publishing", value=npm_trusted_publishing, expected_type=type_hints["npm_trusted_publishing"])
            check_type(argname="argument package_manager", value=package_manager, expected_type=type_hints["package_manager"])
            check_type(argname="argument package_name", value=package_name, expected_type=type_hints["package_name"])
            check_type(argname="argument peer_dependency_options", value=peer_dependency_options, expected_type=type_hints["peer_dependency_options"])
            check_type(argname="argument peer_deps", value=peer_deps, expected_type=type_hints["peer_deps"])
            check_type(argname="argument pnpm_version", value=pnpm_version, expected_type=type_hints["pnpm_version"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument repository_directory", value=repository_directory, expected_type=type_hints["repository_directory"])
            check_type(argname="argument scoped_packages_options", value=scoped_packages_options, expected_type=type_hints["scoped_packages_options"])
            check_type(argname="argument scripts", value=scripts, expected_type=type_hints["scripts"])
            check_type(argname="argument stability", value=stability, expected_type=type_hints["stability"])
            check_type(argname="argument yarn_berry_options", value=yarn_berry_options, expected_type=type_hints["yarn_berry_options"])
            check_type(argname="argument bump_package", value=bump_package, expected_type=type_hints["bump_package"])
            check_type(argname="argument jsii_release_version", value=jsii_release_version, expected_type=type_hints["jsii_release_version"])
            check_type(argname="argument major_version", value=major_version, expected_type=type_hints["major_version"])
            check_type(argname="argument min_major_version", value=min_major_version, expected_type=type_hints["min_major_version"])
            check_type(argname="argument next_version_command", value=next_version_command, expected_type=type_hints["next_version_command"])
            check_type(argname="argument npm_dist_tag", value=npm_dist_tag, expected_type=type_hints["npm_dist_tag"])
            check_type(argname="argument post_build_steps", value=post_build_steps, expected_type=type_hints["post_build_steps"])
            check_type(argname="argument prerelease", value=prerelease, expected_type=type_hints["prerelease"])
            check_type(argname="argument publish_dry_run", value=publish_dry_run, expected_type=type_hints["publish_dry_run"])
            check_type(argname="argument publish_tasks", value=publish_tasks, expected_type=type_hints["publish_tasks"])
            check_type(argname="argument releasable_commits", value=releasable_commits, expected_type=type_hints["releasable_commits"])
            check_type(argname="argument release_branches", value=release_branches, expected_type=type_hints["release_branches"])
            check_type(argname="argument release_environment", value=release_environment, expected_type=type_hints["release_environment"])
            check_type(argname="argument release_every_commit", value=release_every_commit, expected_type=type_hints["release_every_commit"])
            check_type(argname="argument release_failure_issue", value=release_failure_issue, expected_type=type_hints["release_failure_issue"])
            check_type(argname="argument release_failure_issue_label", value=release_failure_issue_label, expected_type=type_hints["release_failure_issue_label"])
            check_type(argname="argument release_schedule", value=release_schedule, expected_type=type_hints["release_schedule"])
            check_type(argname="argument release_tag_prefix", value=release_tag_prefix, expected_type=type_hints["release_tag_prefix"])
            check_type(argname="argument release_trigger", value=release_trigger, expected_type=type_hints["release_trigger"])
            check_type(argname="argument release_workflow_env", value=release_workflow_env, expected_type=type_hints["release_workflow_env"])
            check_type(argname="argument release_workflow_name", value=release_workflow_name, expected_type=type_hints["release_workflow_name"])
            check_type(argname="argument release_workflow_setup_steps", value=release_workflow_setup_steps, expected_type=type_hints["release_workflow_setup_steps"])
            check_type(argname="argument versionrc_options", value=versionrc_options, expected_type=type_hints["versionrc_options"])
            check_type(argname="argument workflow_container_image", value=workflow_container_image, expected_type=type_hints["workflow_container_image"])
            check_type(argname="argument workflow_runs_on", value=workflow_runs_on, expected_type=type_hints["workflow_runs_on"])
            check_type(argname="argument workflow_runs_on_group", value=workflow_runs_on_group, expected_type=type_hints["workflow_runs_on_group"])
            check_type(argname="argument default_release_branch", value=default_release_branch, expected_type=type_hints["default_release_branch"])
            check_type(argname="argument artifacts_directory", value=artifacts_directory, expected_type=type_hints["artifacts_directory"])
            check_type(argname="argument auto_approve_upgrades", value=auto_approve_upgrades, expected_type=type_hints["auto_approve_upgrades"])
            check_type(argname="argument biome", value=biome, expected_type=type_hints["biome"])
            check_type(argname="argument biome_options", value=biome_options, expected_type=type_hints["biome_options"])
            check_type(argname="argument build_workflow", value=build_workflow, expected_type=type_hints["build_workflow"])
            check_type(argname="argument build_workflow_options", value=build_workflow_options, expected_type=type_hints["build_workflow_options"])
            check_type(argname="argument build_workflow_triggers", value=build_workflow_triggers, expected_type=type_hints["build_workflow_triggers"])
            check_type(argname="argument bundler_options", value=bundler_options, expected_type=type_hints["bundler_options"])
            check_type(argname="argument check_licenses", value=check_licenses, expected_type=type_hints["check_licenses"])
            check_type(argname="argument code_cov", value=code_cov, expected_type=type_hints["code_cov"])
            check_type(argname="argument code_cov_token_secret", value=code_cov_token_secret, expected_type=type_hints["code_cov_token_secret"])
            check_type(argname="argument copyright_owner", value=copyright_owner, expected_type=type_hints["copyright_owner"])
            check_type(argname="argument copyright_period", value=copyright_period, expected_type=type_hints["copyright_period"])
            check_type(argname="argument dependabot", value=dependabot, expected_type=type_hints["dependabot"])
            check_type(argname="argument dependabot_options", value=dependabot_options, expected_type=type_hints["dependabot_options"])
            check_type(argname="argument deps_upgrade", value=deps_upgrade, expected_type=type_hints["deps_upgrade"])
            check_type(argname="argument deps_upgrade_options", value=deps_upgrade_options, expected_type=type_hints["deps_upgrade_options"])
            check_type(argname="argument gitignore", value=gitignore, expected_type=type_hints["gitignore"])
            check_type(argname="argument jest", value=jest, expected_type=type_hints["jest"])
            check_type(argname="argument jest_options", value=jest_options, expected_type=type_hints["jest_options"])
            check_type(argname="argument mutable_build", value=mutable_build, expected_type=type_hints["mutable_build"])
            check_type(argname="argument npmignore", value=npmignore, expected_type=type_hints["npmignore"])
            check_type(argname="argument npmignore_enabled", value=npmignore_enabled, expected_type=type_hints["npmignore_enabled"])
            check_type(argname="argument npm_ignore_options", value=npm_ignore_options, expected_type=type_hints["npm_ignore_options"])
            check_type(argname="argument package", value=package, expected_type=type_hints["package"])
            check_type(argname="argument prettier", value=prettier, expected_type=type_hints["prettier"])
            check_type(argname="argument prettier_options", value=prettier_options, expected_type=type_hints["prettier_options"])
            check_type(argname="argument projen_dev_dependency", value=projen_dev_dependency, expected_type=type_hints["projen_dev_dependency"])
            check_type(argname="argument projenrc_js", value=projenrc_js, expected_type=type_hints["projenrc_js"])
            check_type(argname="argument projenrc_js_options", value=projenrc_js_options, expected_type=type_hints["projenrc_js_options"])
            check_type(argname="argument projen_version", value=projen_version, expected_type=type_hints["projen_version"])
            check_type(argname="argument pull_request_template", value=pull_request_template, expected_type=type_hints["pull_request_template"])
            check_type(argname="argument pull_request_template_contents", value=pull_request_template_contents, expected_type=type_hints["pull_request_template_contents"])
            check_type(argname="argument release", value=release, expected_type=type_hints["release"])
            check_type(argname="argument release_to_npm", value=release_to_npm, expected_type=type_hints["release_to_npm"])
            check_type(argname="argument release_workflow", value=release_workflow, expected_type=type_hints["release_workflow"])
            check_type(argname="argument workflow_bootstrap_steps", value=workflow_bootstrap_steps, expected_type=type_hints["workflow_bootstrap_steps"])
            check_type(argname="argument workflow_git_identity", value=workflow_git_identity, expected_type=type_hints["workflow_git_identity"])
            check_type(argname="argument workflow_node_version", value=workflow_node_version, expected_type=type_hints["workflow_node_version"])
            check_type(argname="argument workflow_package_cache", value=workflow_package_cache, expected_type=type_hints["workflow_package_cache"])
            check_type(argname="argument disable_tsconfig", value=disable_tsconfig, expected_type=type_hints["disable_tsconfig"])
            check_type(argname="argument disable_tsconfig_dev", value=disable_tsconfig_dev, expected_type=type_hints["disable_tsconfig_dev"])
            check_type(argname="argument docgen", value=docgen, expected_type=type_hints["docgen"])
            check_type(argname="argument docs_directory", value=docs_directory, expected_type=type_hints["docs_directory"])
            check_type(argname="argument entrypoint_types", value=entrypoint_types, expected_type=type_hints["entrypoint_types"])
            check_type(argname="argument eslint", value=eslint, expected_type=type_hints["eslint"])
            check_type(argname="argument eslint_options", value=eslint_options, expected_type=type_hints["eslint_options"])
            check_type(argname="argument libdir", value=libdir, expected_type=type_hints["libdir"])
            check_type(argname="argument projenrc_ts", value=projenrc_ts, expected_type=type_hints["projenrc_ts"])
            check_type(argname="argument projenrc_ts_options", value=projenrc_ts_options, expected_type=type_hints["projenrc_ts_options"])
            check_type(argname="argument sample_code", value=sample_code, expected_type=type_hints["sample_code"])
            check_type(argname="argument srcdir", value=srcdir, expected_type=type_hints["srcdir"])
            check_type(argname="argument testdir", value=testdir, expected_type=type_hints["testdir"])
            check_type(argname="argument tsconfig", value=tsconfig, expected_type=type_hints["tsconfig"])
            check_type(argname="argument tsconfig_dev", value=tsconfig_dev, expected_type=type_hints["tsconfig_dev"])
            check_type(argname="argument tsconfig_dev_file", value=tsconfig_dev_file, expected_type=type_hints["tsconfig_dev_file"])
            check_type(argname="argument ts_jest_options", value=ts_jest_options, expected_type=type_hints["ts_jest_options"])
            check_type(argname="argument typescript_version", value=typescript_version, expected_type=type_hints["typescript_version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "default_release_branch": default_release_branch,
        }
        if commit_generated is not None:
            self._values["commit_generated"] = commit_generated
        if git_ignore_options is not None:
            self._values["git_ignore_options"] = git_ignore_options
        if git_options is not None:
            self._values["git_options"] = git_options
        if logging is not None:
            self._values["logging"] = logging
        if outdir is not None:
            self._values["outdir"] = outdir
        if parent is not None:
            self._values["parent"] = parent
        if projen_command is not None:
            self._values["projen_command"] = projen_command
        if projenrc_json is not None:
            self._values["projenrc_json"] = projenrc_json
        if projenrc_json_options is not None:
            self._values["projenrc_json_options"] = projenrc_json_options
        if renovatebot is not None:
            self._values["renovatebot"] = renovatebot
        if renovatebot_options is not None:
            self._values["renovatebot_options"] = renovatebot_options
        if auto_approve_options is not None:
            self._values["auto_approve_options"] = auto_approve_options
        if auto_merge is not None:
            self._values["auto_merge"] = auto_merge
        if auto_merge_options is not None:
            self._values["auto_merge_options"] = auto_merge_options
        if clobber is not None:
            self._values["clobber"] = clobber
        if dev_container is not None:
            self._values["dev_container"] = dev_container
        if github is not None:
            self._values["github"] = github
        if github_options is not None:
            self._values["github_options"] = github_options
        if gitpod is not None:
            self._values["gitpod"] = gitpod
        if mergify is not None:
            self._values["mergify"] = mergify
        if mergify_options is not None:
            self._values["mergify_options"] = mergify_options
        if project_type is not None:
            self._values["project_type"] = project_type
        if projen_credentials is not None:
            self._values["projen_credentials"] = projen_credentials
        if projen_token_secret is not None:
            self._values["projen_token_secret"] = projen_token_secret
        if readme is not None:
            self._values["readme"] = readme
        if stale is not None:
            self._values["stale"] = stale
        if stale_options is not None:
            self._values["stale_options"] = stale_options
        if vscode is not None:
            self._values["vscode"] = vscode
        if allow_library_dependencies is not None:
            self._values["allow_library_dependencies"] = allow_library_dependencies
        if author_email is not None:
            self._values["author_email"] = author_email
        if author_name is not None:
            self._values["author_name"] = author_name
        if author_organization is not None:
            self._values["author_organization"] = author_organization
        if author_url is not None:
            self._values["author_url"] = author_url
        if auto_detect_bin is not None:
            self._values["auto_detect_bin"] = auto_detect_bin
        if bin is not None:
            self._values["bin"] = bin
        if bugs_email is not None:
            self._values["bugs_email"] = bugs_email
        if bugs_url is not None:
            self._values["bugs_url"] = bugs_url
        if bundled_deps is not None:
            self._values["bundled_deps"] = bundled_deps
        if bun_version is not None:
            self._values["bun_version"] = bun_version
        if code_artifact_options is not None:
            self._values["code_artifact_options"] = code_artifact_options
        if deps is not None:
            self._values["deps"] = deps
        if description is not None:
            self._values["description"] = description
        if dev_deps is not None:
            self._values["dev_deps"] = dev_deps
        if entrypoint is not None:
            self._values["entrypoint"] = entrypoint
        if homepage is not None:
            self._values["homepage"] = homepage
        if keywords is not None:
            self._values["keywords"] = keywords
        if license is not None:
            self._values["license"] = license
        if licensed is not None:
            self._values["licensed"] = licensed
        if max_node_version is not None:
            self._values["max_node_version"] = max_node_version
        if min_node_version is not None:
            self._values["min_node_version"] = min_node_version
        if npm_access is not None:
            self._values["npm_access"] = npm_access
        if npm_provenance is not None:
            self._values["npm_provenance"] = npm_provenance
        if npm_registry is not None:
            self._values["npm_registry"] = npm_registry
        if npm_registry_url is not None:
            self._values["npm_registry_url"] = npm_registry_url
        if npm_token_secret is not None:
            self._values["npm_token_secret"] = npm_token_secret
        if npm_trusted_publishing is not None:
            self._values["npm_trusted_publishing"] = npm_trusted_publishing
        if package_manager is not None:
            self._values["package_manager"] = package_manager
        if package_name is not None:
            self._values["package_name"] = package_name
        if peer_dependency_options is not None:
            self._values["peer_dependency_options"] = peer_dependency_options
        if peer_deps is not None:
            self._values["peer_deps"] = peer_deps
        if pnpm_version is not None:
            self._values["pnpm_version"] = pnpm_version
        if repository is not None:
            self._values["repository"] = repository
        if repository_directory is not None:
            self._values["repository_directory"] = repository_directory
        if scoped_packages_options is not None:
            self._values["scoped_packages_options"] = scoped_packages_options
        if scripts is not None:
            self._values["scripts"] = scripts
        if stability is not None:
            self._values["stability"] = stability
        if yarn_berry_options is not None:
            self._values["yarn_berry_options"] = yarn_berry_options
        if bump_package is not None:
            self._values["bump_package"] = bump_package
        if jsii_release_version is not None:
            self._values["jsii_release_version"] = jsii_release_version
        if major_version is not None:
            self._values["major_version"] = major_version
        if min_major_version is not None:
            self._values["min_major_version"] = min_major_version
        if next_version_command is not None:
            self._values["next_version_command"] = next_version_command
        if npm_dist_tag is not None:
            self._values["npm_dist_tag"] = npm_dist_tag
        if post_build_steps is not None:
            self._values["post_build_steps"] = post_build_steps
        if prerelease is not None:
            self._values["prerelease"] = prerelease
        if publish_dry_run is not None:
            self._values["publish_dry_run"] = publish_dry_run
        if publish_tasks is not None:
            self._values["publish_tasks"] = publish_tasks
        if releasable_commits is not None:
            self._values["releasable_commits"] = releasable_commits
        if release_branches is not None:
            self._values["release_branches"] = release_branches
        if release_environment is not None:
            self._values["release_environment"] = release_environment
        if release_every_commit is not None:
            self._values["release_every_commit"] = release_every_commit
        if release_failure_issue is not None:
            self._values["release_failure_issue"] = release_failure_issue
        if release_failure_issue_label is not None:
            self._values["release_failure_issue_label"] = release_failure_issue_label
        if release_schedule is not None:
            self._values["release_schedule"] = release_schedule
        if release_tag_prefix is not None:
            self._values["release_tag_prefix"] = release_tag_prefix
        if release_trigger is not None:
            self._values["release_trigger"] = release_trigger
        if release_workflow_env is not None:
            self._values["release_workflow_env"] = release_workflow_env
        if release_workflow_name is not None:
            self._values["release_workflow_name"] = release_workflow_name
        if release_workflow_setup_steps is not None:
            self._values["release_workflow_setup_steps"] = release_workflow_setup_steps
        if versionrc_options is not None:
            self._values["versionrc_options"] = versionrc_options
        if workflow_container_image is not None:
            self._values["workflow_container_image"] = workflow_container_image
        if workflow_runs_on is not None:
            self._values["workflow_runs_on"] = workflow_runs_on
        if workflow_runs_on_group is not None:
            self._values["workflow_runs_on_group"] = workflow_runs_on_group
        if artifacts_directory is not None:
            self._values["artifacts_directory"] = artifacts_directory
        if auto_approve_upgrades is not None:
            self._values["auto_approve_upgrades"] = auto_approve_upgrades
        if biome is not None:
            self._values["biome"] = biome
        if biome_options is not None:
            self._values["biome_options"] = biome_options
        if build_workflow is not None:
            self._values["build_workflow"] = build_workflow
        if build_workflow_options is not None:
            self._values["build_workflow_options"] = build_workflow_options
        if build_workflow_triggers is not None:
            self._values["build_workflow_triggers"] = build_workflow_triggers
        if bundler_options is not None:
            self._values["bundler_options"] = bundler_options
        if check_licenses is not None:
            self._values["check_licenses"] = check_licenses
        if code_cov is not None:
            self._values["code_cov"] = code_cov
        if code_cov_token_secret is not None:
            self._values["code_cov_token_secret"] = code_cov_token_secret
        if copyright_owner is not None:
            self._values["copyright_owner"] = copyright_owner
        if copyright_period is not None:
            self._values["copyright_period"] = copyright_period
        if dependabot is not None:
            self._values["dependabot"] = dependabot
        if dependabot_options is not None:
            self._values["dependabot_options"] = dependabot_options
        if deps_upgrade is not None:
            self._values["deps_upgrade"] = deps_upgrade
        if deps_upgrade_options is not None:
            self._values["deps_upgrade_options"] = deps_upgrade_options
        if gitignore is not None:
            self._values["gitignore"] = gitignore
        if jest is not None:
            self._values["jest"] = jest
        if jest_options is not None:
            self._values["jest_options"] = jest_options
        if mutable_build is not None:
            self._values["mutable_build"] = mutable_build
        if npmignore is not None:
            self._values["npmignore"] = npmignore
        if npmignore_enabled is not None:
            self._values["npmignore_enabled"] = npmignore_enabled
        if npm_ignore_options is not None:
            self._values["npm_ignore_options"] = npm_ignore_options
        if package is not None:
            self._values["package"] = package
        if prettier is not None:
            self._values["prettier"] = prettier
        if prettier_options is not None:
            self._values["prettier_options"] = prettier_options
        if projen_dev_dependency is not None:
            self._values["projen_dev_dependency"] = projen_dev_dependency
        if projenrc_js is not None:
            self._values["projenrc_js"] = projenrc_js
        if projenrc_js_options is not None:
            self._values["projenrc_js_options"] = projenrc_js_options
        if projen_version is not None:
            self._values["projen_version"] = projen_version
        if pull_request_template is not None:
            self._values["pull_request_template"] = pull_request_template
        if pull_request_template_contents is not None:
            self._values["pull_request_template_contents"] = pull_request_template_contents
        if release is not None:
            self._values["release"] = release
        if release_to_npm is not None:
            self._values["release_to_npm"] = release_to_npm
        if release_workflow is not None:
            self._values["release_workflow"] = release_workflow
        if workflow_bootstrap_steps is not None:
            self._values["workflow_bootstrap_steps"] = workflow_bootstrap_steps
        if workflow_git_identity is not None:
            self._values["workflow_git_identity"] = workflow_git_identity
        if workflow_node_version is not None:
            self._values["workflow_node_version"] = workflow_node_version
        if workflow_package_cache is not None:
            self._values["workflow_package_cache"] = workflow_package_cache
        if disable_tsconfig is not None:
            self._values["disable_tsconfig"] = disable_tsconfig
        if disable_tsconfig_dev is not None:
            self._values["disable_tsconfig_dev"] = disable_tsconfig_dev
        if docgen is not None:
            self._values["docgen"] = docgen
        if docs_directory is not None:
            self._values["docs_directory"] = docs_directory
        if entrypoint_types is not None:
            self._values["entrypoint_types"] = entrypoint_types
        if eslint is not None:
            self._values["eslint"] = eslint
        if eslint_options is not None:
            self._values["eslint_options"] = eslint_options
        if libdir is not None:
            self._values["libdir"] = libdir
        if projenrc_ts is not None:
            self._values["projenrc_ts"] = projenrc_ts
        if projenrc_ts_options is not None:
            self._values["projenrc_ts_options"] = projenrc_ts_options
        if sample_code is not None:
            self._values["sample_code"] = sample_code
        if srcdir is not None:
            self._values["srcdir"] = srcdir
        if testdir is not None:
            self._values["testdir"] = testdir
        if tsconfig is not None:
            self._values["tsconfig"] = tsconfig
        if tsconfig_dev is not None:
            self._values["tsconfig_dev"] = tsconfig_dev
        if tsconfig_dev_file is not None:
            self._values["tsconfig_dev_file"] = tsconfig_dev_file
        if ts_jest_options is not None:
            self._values["ts_jest_options"] = ts_jest_options
        if typescript_version is not None:
            self._values["typescript_version"] = typescript_version

    @builtins.property
    def name(self) -> builtins.str:
        '''(experimental) This is the name of your project.

        :default: $BASEDIR

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def commit_generated(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Whether to commit the managed files by default.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("commit_generated")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def git_ignore_options(self) -> typing.Optional[_IgnoreFileOptions_86c48b91]:
        '''(experimental) Configuration options for .gitignore file.

        :stability: experimental
        '''
        result = self._values.get("git_ignore_options")
        return typing.cast(typing.Optional[_IgnoreFileOptions_86c48b91], result)

    @builtins.property
    def git_options(self) -> typing.Optional[_GitOptions_a65916a3]:
        '''(experimental) Configuration options for git.

        :stability: experimental
        '''
        result = self._values.get("git_options")
        return typing.cast(typing.Optional[_GitOptions_a65916a3], result)

    @builtins.property
    def logging(self) -> typing.Optional[_LoggerOptions_eb0f6309]:
        '''(experimental) Configure logging options such as verbosity.

        :default: {}

        :stability: experimental
        '''
        result = self._values.get("logging")
        return typing.cast(typing.Optional[_LoggerOptions_eb0f6309], result)

    @builtins.property
    def outdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) The root directory of the project.

        Relative to this directory, all files are synthesized.

        If this project has a parent, this directory is relative to the parent
        directory and it cannot be the same as the parent or any of it's other
        subprojects.

        :default: "."

        :stability: experimental
        '''
        result = self._values.get("outdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent(self) -> typing.Optional[_Project_57d89203]:
        '''(experimental) The parent project, if this project is part of a bigger project.

        :stability: experimental
        '''
        result = self._values.get("parent")
        return typing.cast(typing.Optional[_Project_57d89203], result)

    @builtins.property
    def projen_command(self) -> typing.Optional[builtins.str]:
        '''(experimental) The shell command to use in order to run the projen CLI.

        Can be used to customize in special environments.

        :default: "npx projen"

        :stability: experimental
        '''
        result = self._values.get("projen_command")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projenrc_json(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate (once) .projenrc.json (in JSON). Set to ``false`` in order to disable .projenrc.json generation.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("projenrc_json")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_json_options(self) -> typing.Optional[_ProjenrcJsonOptions_9c40dd4f]:
        '''(experimental) Options for .projenrc.json.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("projenrc_json_options")
        return typing.cast(typing.Optional[_ProjenrcJsonOptions_9c40dd4f], result)

    @builtins.property
    def renovatebot(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use renovatebot to handle dependency upgrades.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("renovatebot")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def renovatebot_options(self) -> typing.Optional[_RenovatebotOptions_18e6b8a1]:
        '''(experimental) Options for renovatebot.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("renovatebot_options")
        return typing.cast(typing.Optional[_RenovatebotOptions_18e6b8a1], result)

    @builtins.property
    def auto_approve_options(self) -> typing.Optional[_AutoApproveOptions_dac86cbe]:
        '''(experimental) Enable and configure the 'auto approve' workflow.

        :default: - auto approve is disabled

        :stability: experimental
        '''
        result = self._values.get("auto_approve_options")
        return typing.cast(typing.Optional[_AutoApproveOptions_dac86cbe], result)

    @builtins.property
    def auto_merge(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable automatic merging on GitHub.

        Has no effect if ``github.mergify``
        is set to false.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("auto_merge")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def auto_merge_options(self) -> typing.Optional[_AutoMergeOptions_d112cd3c]:
        '''(experimental) Configure options for automatic merging on GitHub.

        Has no effect if
        ``github.mergify`` or ``autoMerge`` is set to false.

        :default: - see defaults in ``AutoMergeOptions``

        :stability: experimental
        '''
        result = self._values.get("auto_merge_options")
        return typing.cast(typing.Optional[_AutoMergeOptions_d112cd3c], result)

    @builtins.property
    def clobber(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a ``clobber`` task which resets the repo to origin.

        :default: - true, but false for subprojects

        :stability: experimental
        '''
        result = self._values.get("clobber")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dev_container(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a VSCode development environment (used for GitHub Codespaces).

        :default: false

        :stability: experimental
        '''
        result = self._values.get("dev_container")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def github(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable GitHub integration.

        Enabled by default for root projects. Disabled for non-root projects.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("github")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def github_options(self) -> typing.Optional[_GitHubOptions_21553699]:
        '''(experimental) Options for GitHub integration.

        :default: - see GitHubOptions

        :stability: experimental
        '''
        result = self._values.get("github_options")
        return typing.cast(typing.Optional[_GitHubOptions_21553699], result)

    @builtins.property
    def gitpod(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add a Gitpod development environment.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("gitpod")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def mergify(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Whether mergify should be enabled on this repository or not.

        :default: true

        :deprecated: use ``githubOptions.mergify`` instead

        :stability: deprecated
        '''
        result = self._values.get("mergify")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def mergify_options(self) -> typing.Optional[_MergifyOptions_a6faaab3]:
        '''(deprecated) Options for mergify.

        :default: - default options

        :deprecated: use ``githubOptions.mergifyOptions`` instead

        :stability: deprecated
        '''
        result = self._values.get("mergify_options")
        return typing.cast(typing.Optional[_MergifyOptions_a6faaab3], result)

    @builtins.property
    def project_type(self) -> typing.Optional[_ProjectType_fd80c725]:
        '''(deprecated) Which type of project this is (library/app).

        :default: ProjectType.UNKNOWN

        :deprecated: no longer supported at the base project level

        :stability: deprecated
        '''
        result = self._values.get("project_type")
        return typing.cast(typing.Optional[_ProjectType_fd80c725], result)

    @builtins.property
    def projen_credentials(self) -> typing.Optional[_GithubCredentials_ae257072]:
        '''(experimental) Choose a method of providing GitHub API access for projen workflows.

        :default: - use a personal access token named PROJEN_GITHUB_TOKEN

        :stability: experimental
        '''
        result = self._values.get("projen_credentials")
        return typing.cast(typing.Optional[_GithubCredentials_ae257072], result)

    @builtins.property
    def projen_token_secret(self) -> typing.Optional[builtins.str]:
        '''(deprecated) The name of a secret which includes a GitHub Personal Access Token to be used by projen workflows.

        This token needs to have the ``repo``, ``workflows``
        and ``packages`` scope.

        :default: "PROJEN_GITHUB_TOKEN"

        :deprecated: use ``projenCredentials``

        :stability: deprecated
        '''
        result = self._values.get("projen_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def readme(self) -> typing.Optional[_SampleReadmeProps_3518b03b]:
        '''(experimental) The README setup.

        :default: - { filename: 'README.md', contents: '# replace this' }

        :stability: experimental

        Example::

            "{ filename: 'readme.md', contents: '# title' }"
        '''
        result = self._values.get("readme")
        return typing.cast(typing.Optional[_SampleReadmeProps_3518b03b], result)

    @builtins.property
    def stale(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Auto-close of stale issues and pull request.

        See ``staleOptions`` for options.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("stale")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def stale_options(self) -> typing.Optional[_StaleOptions_929db764]:
        '''(experimental) Auto-close stale issues and pull requests.

        To disable set ``stale`` to ``false``.

        :default: - see defaults in ``StaleOptions``

        :stability: experimental
        '''
        result = self._values.get("stale_options")
        return typing.cast(typing.Optional[_StaleOptions_929db764], result)

    @builtins.property
    def vscode(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable VSCode integration.

        Enabled by default for root projects. Disabled for non-root projects.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("vscode")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def allow_library_dependencies(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Allow the project to include ``peerDependencies`` and ``bundledDependencies``.

        This is normally only allowed for libraries. For apps, there's no meaning
        for specifying these.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("allow_library_dependencies")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def author_email(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's e-mail.

        :stability: experimental
        '''
        result = self._values.get("author_email")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def author_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's name.

        :stability: experimental
        '''
        result = self._values.get("author_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def author_organization(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Is the author an organization.

        :stability: experimental
        '''
        result = self._values.get("author_organization")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def author_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) Author's URL / Website.

        :stability: experimental
        '''
        result = self._values.get("author_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auto_detect_bin(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically add all executables under the ``bin`` directory to your ``package.json`` file under the ``bin`` section.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("auto_detect_bin")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def bin(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Binary programs vended with your module.

        You can use this option to add/customize how binaries are represented in
        your ``package.json``, but unless ``autoDetectBin`` is ``false``, every
        executable file under ``bin`` will automatically be added to this section.

        :stability: experimental
        '''
        result = self._values.get("bin")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def bugs_email(self) -> typing.Optional[builtins.str]:
        '''(experimental) The email address to which issues should be reported.

        :stability: experimental
        '''
        result = self._values.get("bugs_email")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bugs_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) The url to your project's issue tracker.

        :stability: experimental
        '''
        result = self._values.get("bugs_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bundled_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) List of dependencies to bundle into this module.

        These modules will be
        added both to the ``dependencies`` section and ``bundledDependencies`` section of
        your ``package.json``.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :stability: experimental
        '''
        result = self._values.get("bundled_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def bun_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of Bun to use if using Bun as a package manager.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("bun_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def code_artifact_options(self) -> typing.Optional[_CodeArtifactOptions_e4782b3e]:
        '''(experimental) Options for npm packages using AWS CodeArtifact.

        This is required if publishing packages to, or installing scoped packages from AWS CodeArtifact

        :default: - undefined

        :stability: experimental
        '''
        result = self._values.get("code_artifact_options")
        return typing.cast(typing.Optional[_CodeArtifactOptions_e4782b3e], result)

    @builtins.property
    def deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Runtime dependencies of this module.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :default: []

        :stability: experimental
        :featured: true

        Example::

            [ 'express', 'lodash', 'foo@^2' ]
        '''
        result = self._values.get("deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''(experimental) The description is just a string that helps people understand the purpose of the package.

        It can be used when searching for packages in a package manager as well.
        See https://classic.yarnpkg.com/en/docs/package-json/#toc-description

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dev_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Build dependencies for this module.

        These dependencies will only be
        available in your build environment but will not be fetched when this
        module is consumed.

        The recommendation is to only specify the module name here (e.g.
        ``express``). This will behave similar to ``yarn add`` or ``npm install`` in the
        sense that it will add the module as a dependency to your ``package.json``
        file with the latest version (``^``). You can specify semver requirements in
        the same syntax passed to ``npm i`` or ``yarn add`` (e.g. ``express@^2``) and
        this will be what you ``package.json`` will eventually include.

        :default: []

        :stability: experimental
        :featured: true

        Example::

            [ 'typescript', '@types/express' ]
        '''
        result = self._values.get("dev_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def entrypoint(self) -> typing.Optional[builtins.str]:
        '''(experimental) Module entrypoint (``main`` in ``package.json``).

        Set to an empty string to not include ``main`` in your package.json

        :default: "lib/index.js"

        :stability: experimental
        '''
        result = self._values.get("entrypoint")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def homepage(self) -> typing.Optional[builtins.str]:
        '''(experimental) Package's Homepage / Website.

        :stability: experimental
        '''
        result = self._values.get("homepage")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def keywords(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Keywords to include in ``package.json``.

        :stability: experimental
        '''
        result = self._values.get("keywords")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def license(self) -> typing.Optional[builtins.str]:
        '''(experimental) License's SPDX identifier.

        See https://github.com/projen/projen/tree/main/license-text for a list of supported licenses.
        Use the ``licensed`` option if you want to no license to be specified.

        :default: "Apache-2.0"

        :stability: experimental
        '''
        result = self._values.get("license")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def licensed(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Indicates if a license should be added.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("licensed")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def max_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The maximum node version supported by this package. Most projects should not use this option.

        The value indicates that the package is incompatible with any newer versions of node.
        This requirement is enforced via the engines field.

        You will normally not need to set this option.
        Consider this option only if your package is known to not function with newer versions of node.

        :default: - no maximum version is enforced

        :stability: experimental
        '''
        result = self._values.get("max_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def min_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The minimum node version required by this package to function. Most projects should not use this option.

        The value indicates that the package is incompatible with any older versions of node.
        This requirement is enforced via the engines field.

        You will normally not need to set this option, even if your package is incompatible with EOL versions of node.
        Consider this option only if your package depends on a specific feature, that is not available in other LTS versions.
        Setting this option has very high impact on the consumers of your package,
        as package managers will actively prevent usage with node versions you have marked as incompatible.

        To change the node version of your CI/CD workflows, use ``workflowNodeVersion``.

        :default: - no minimum version is enforced

        :stability: experimental
        '''
        result = self._values.get("min_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_access(self) -> typing.Optional[_NpmAccess_134fa228]:
        '''(experimental) Access level of the npm package.

        :default:

        - for scoped packages (e.g. ``foo@bar``), the default is
        ``NpmAccess.RESTRICTED``, for non-scoped packages, the default is
        ``NpmAccess.PUBLIC``.

        :stability: experimental
        '''
        result = self._values.get("npm_access")
        return typing.cast(typing.Optional[_NpmAccess_134fa228], result)

    @builtins.property
    def npm_provenance(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Should provenance statements be generated when the package is published.

        A supported package manager is required to publish a package with npm provenance statements and
        you will need to use a supported CI/CD provider.

        Note that the projen ``Release`` and ``Publisher`` components are using ``publib`` to publish packages,
        which is using npm internally and supports provenance statements independently of the package manager used.

        :default: - true for public packages, false otherwise

        :see: https://docs.npmjs.com/generating-provenance-statements
        :stability: experimental
        '''
        result = self._values.get("npm_provenance")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npm_registry(self) -> typing.Optional[builtins.str]:
        '''(deprecated) The host name of the npm registry to publish to.

        Cannot be set together with ``npmRegistryUrl``.

        :deprecated: use ``npmRegistryUrl`` instead

        :stability: deprecated
        '''
        result = self._values.get("npm_registry")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_registry_url(self) -> typing.Optional[builtins.str]:
        '''(experimental) The base URL of the npm package registry.

        Must be a URL (e.g. start with "https://" or "http://")

        :default: "https://registry.npmjs.org"

        :stability: experimental
        '''
        result = self._values.get("npm_registry_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_token_secret(self) -> typing.Optional[builtins.str]:
        '''(experimental) GitHub secret which contains the NPM token to use when publishing packages.

        :default: "NPM_TOKEN"

        :stability: experimental
        '''
        result = self._values.get("npm_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_trusted_publishing(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use trusted publishing for publishing to npmjs.com Needs to be pre-configured on npm.js to work.

        :default: - false

        :stability: experimental
        '''
        result = self._values.get("npm_trusted_publishing")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def package_manager(self) -> typing.Optional[_NodePackageManager_3eb53bf6]:
        '''(experimental) The Node Package Manager used to execute scripts.

        :default: NodePackageManager.YARN_CLASSIC

        :stability: experimental
        '''
        result = self._values.get("package_manager")
        return typing.cast(typing.Optional[_NodePackageManager_3eb53bf6], result)

    @builtins.property
    def package_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The "name" in package.json.

        :default: - defaults to project name

        :stability: experimental
        :featured: true
        '''
        result = self._values.get("package_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def peer_dependency_options(
        self,
    ) -> typing.Optional[_PeerDependencyOptions_99d7d493]:
        '''(experimental) Options for ``peerDeps``.

        :stability: experimental
        '''
        result = self._values.get("peer_dependency_options")
        return typing.cast(typing.Optional[_PeerDependencyOptions_99d7d493], result)

    @builtins.property
    def peer_deps(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Peer dependencies for this module.

        Dependencies listed here are required to
        be installed (and satisfied) by the *consumer* of this library. Using peer
        dependencies allows you to ensure that only a single module of a certain
        library exists in the ``node_modules`` tree of your consumers.

        Note that prior to npm@7, peer dependencies are *not* automatically
        installed, which means that adding peer dependencies to a library will be a
        breaking change for your customers.

        Unless ``peerDependencyOptions.pinnedDevDependency`` is disabled (it is
        enabled by default), projen will automatically add a dev dependency with a
        pinned version for each peer dependency. This will ensure that you build &
        test your module against the lowest peer version required.

        :default: []

        :stability: experimental
        '''
        result = self._values.get("peer_deps")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def pnpm_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The version of PNPM to use if using PNPM as a package manager.

        :default: "9"

        :stability: experimental
        '''
        result = self._values.get("pnpm_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repository(self) -> typing.Optional[builtins.str]:
        '''(experimental) The repository is the location where the actual code for your package lives.

        See https://classic.yarnpkg.com/en/docs/package-json/#toc-repository

        :stability: experimental
        '''
        result = self._values.get("repository")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repository_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) If the package.json for your package is not in the root directory (for example if it is part of a monorepo), you can specify the directory in which it lives.

        :stability: experimental
        '''
        result = self._values.get("repository_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scoped_packages_options(
        self,
    ) -> typing.Optional[typing.List[_ScopedPackagesOptions_52f0a477]]:
        '''(experimental) Options for privately hosted scoped packages.

        :default: - fetch all scoped packages from the public npm registry

        :stability: experimental
        '''
        result = self._values.get("scoped_packages_options")
        return typing.cast(typing.Optional[typing.List[_ScopedPackagesOptions_52f0a477]], result)

    @builtins.property
    def scripts(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(deprecated) npm scripts to include.

        If a script has the same name as a standard script,
        the standard script will be overwritten.
        Also adds the script as a task.

        :default: {}

        :deprecated: use ``project.addTask()`` or ``package.setScript()``

        :stability: deprecated
        '''
        result = self._values.get("scripts")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def stability(self) -> typing.Optional[builtins.str]:
        '''(experimental) Package's Stability.

        :stability: experimental
        '''
        result = self._values.get("stability")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def yarn_berry_options(self) -> typing.Optional[_YarnBerryOptions_b6942539]:
        '''(experimental) Options for Yarn Berry.

        :default: - Yarn Berry v4 with all default options

        :stability: experimental
        '''
        result = self._values.get("yarn_berry_options")
        return typing.cast(typing.Optional[_YarnBerryOptions_b6942539], result)

    @builtins.property
    def bump_package(self) -> typing.Optional[builtins.str]:
        '''(experimental) The ``commit-and-tag-version`` compatible package used to bump the package version, as a dependency string.

        This can be any compatible package version, including the deprecated ``standard-version@9``.

        :default: - A recent version of "commit-and-tag-version"

        :stability: experimental
        '''
        result = self._values.get("bump_package")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def jsii_release_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) Version requirement of ``publib`` which is used to publish modules to npm.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("jsii_release_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def major_version(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Major version to release from the default branch.

        If this is specified, we bump the latest version of this major version line.
        If not specified, we bump the global latest version.

        :default: - Major version is not enforced.

        :stability: experimental
        '''
        result = self._values.get("major_version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_major_version(self) -> typing.Optional[jsii.Number]:
        '''(experimental) Minimal Major version to release.

        This can be useful to set to 1, as breaking changes before the 1.x major
        release are not incrementing the major version number.

        Can not be set together with ``majorVersion``.

        :default: - No minimum version is being enforced

        :stability: experimental
        '''
        result = self._values.get("min_major_version")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def next_version_command(self) -> typing.Optional[builtins.str]:
        '''(experimental) A shell command to control the next version to release.

        If present, this shell command will be run before the bump is executed, and
        it determines what version to release. It will be executed in the following
        environment:

        - Working directory: the project directory.
        - ``$VERSION``: the current version. Looks like ``1.2.3``.
        - ``$LATEST_TAG``: the most recent tag. Looks like ``prefix-v1.2.3``, or may be unset.
        - ``$SUGGESTED_BUMP``: the suggested bump action based on commits. One of ``major|minor|patch|none``.

        The command should print one of the following to ``stdout``:

        - Nothing: the next version number will be determined based on commit history.
        - ``x.y.z``: the next version number will be ``x.y.z``.
        - ``major|minor|patch``: the next version number will be the current version number
          with the indicated component bumped.

        This setting cannot be specified together with ``minMajorVersion``; the invoked
        script can be used to achieve the effects of ``minMajorVersion``.

        :default: - The next version will be determined based on the commit history and project settings.

        :stability: experimental
        '''
        result = self._values.get("next_version_command")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def npm_dist_tag(self) -> typing.Optional[builtins.str]:
        '''(experimental) The npmDistTag to use when publishing from the default branch.

        To set the npm dist-tag for release branches, set the ``npmDistTag`` property
        for each branch.

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("npm_dist_tag")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def post_build_steps(self) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) Steps to execute after build as part of the release workflow.

        :default: []

        :stability: experimental
        '''
        result = self._values.get("post_build_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def prerelease(self) -> typing.Optional[builtins.str]:
        '''(experimental) Bump versions from the default branch as pre-releases (e.g. "beta", "alpha", "pre").

        :default: - normal semantic versions

        :stability: experimental
        '''
        result = self._values.get("prerelease")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def publish_dry_run(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Instead of actually publishing to package managers, just print the publishing command.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("publish_dry_run")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def publish_tasks(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define publishing tasks that can be executed manually as well as workflows.

        Normally, publishing only happens within automated workflows. Enable this
        in order to create a publishing task for each publishing activity.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("publish_tasks")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def releasable_commits(self) -> typing.Optional[_ReleasableCommits_d481ce10]:
        '''(experimental) Find commits that should be considered releasable Used to decide if a release is required.

        :default: ReleasableCommits.everyCommit()

        :stability: experimental
        '''
        result = self._values.get("releasable_commits")
        return typing.cast(typing.Optional[_ReleasableCommits_d481ce10], result)

    @builtins.property
    def release_branches(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, _BranchOptions_13663d08]]:
        '''(experimental) Defines additional release branches.

        A workflow will be created for each
        release branch which will publish releases from commits in this branch.
        Each release branch *must* be assigned a major version number which is used
        to enforce that versions published from that branch always use that major
        version. If multiple branches are used, the ``majorVersion`` field must also
        be provided for the default branch.

        :default:

        - no additional branches are used for release. you can use
        ``addBranch()`` to add additional branches.

        :stability: experimental
        '''
        result = self._values.get("release_branches")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, _BranchOptions_13663d08]], result)

    @builtins.property
    def release_environment(self) -> typing.Optional[builtins.str]:
        '''(experimental) The GitHub Actions environment used for the release.

        This can be used to add an explicit approval step to the release
        or limit who can initiate a release through environment protection rules.

        When multiple artifacts are released, the environment can be overwritten
        on a per artifact basis.

        :default: - no environment used, unless set at the artifact level

        :stability: experimental
        '''
        result = self._values.get("release_environment")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_every_commit(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Automatically release new versions every commit to one of branches in ``releaseBranches``.

        :default: true

        :deprecated: Use ``releaseTrigger: ReleaseTrigger.continuous()`` instead

        :stability: deprecated
        '''
        result = self._values.get("release_every_commit")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_failure_issue(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Create a github issue on every failed publishing task.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("release_failure_issue")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_failure_issue_label(self) -> typing.Optional[builtins.str]:
        '''(experimental) The label to apply to issues indicating publish failures.

        Only applies if ``releaseFailureIssue`` is true.

        :default: "failed-release"

        :stability: experimental
        '''
        result = self._values.get("release_failure_issue_label")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_schedule(self) -> typing.Optional[builtins.str]:
        '''(deprecated) CRON schedule to trigger new releases.

        :default: - no scheduled releases

        :deprecated: Use ``releaseTrigger: ReleaseTrigger.scheduled()`` instead

        :stability: deprecated
        '''
        result = self._values.get("release_schedule")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_tag_prefix(self) -> typing.Optional[builtins.str]:
        '''(experimental) Automatically add the given prefix to release tags. Useful if you are releasing on multiple branches with overlapping version numbers.

        Note: this prefix is used to detect the latest tagged version
        when bumping, so if you change this on a project with an existing version
        history, you may need to manually tag your latest release
        with the new prefix.

        :default: "v"

        :stability: experimental
        '''
        result = self._values.get("release_tag_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_trigger(self) -> typing.Optional[_ReleaseTrigger_e4dc221f]:
        '''(experimental) The release trigger to use.

        :default: - Continuous releases (``ReleaseTrigger.continuous()``)

        :stability: experimental
        '''
        result = self._values.get("release_trigger")
        return typing.cast(typing.Optional[_ReleaseTrigger_e4dc221f], result)

    @builtins.property
    def release_workflow_env(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''(experimental) Build environment variables for release workflows.

        :default: {}

        :stability: experimental
        '''
        result = self._values.get("release_workflow_env")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def release_workflow_name(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the default release workflow.

        :default: "release"

        :stability: experimental
        '''
        result = self._values.get("release_workflow_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def release_workflow_setup_steps(
        self,
    ) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) A set of workflow steps to execute in order to setup the workflow container.

        :stability: experimental
        '''
        result = self._values.get("release_workflow_setup_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def versionrc_options(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''(experimental) Custom configuration used when creating changelog with commit-and-tag-version package.

        Given values either append to default configuration or overwrite values in it.

        :default: - standard configuration applicable for GitHub repositories

        :stability: experimental
        '''
        result = self._values.get("versionrc_options")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def workflow_container_image(self) -> typing.Optional[builtins.str]:
        '''(experimental) Container image to use for GitHub workflows.

        :default: - default image

        :stability: experimental
        '''
        result = self._values.get("workflow_container_image")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workflow_runs_on(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Github Runner selection labels.

        :default: ["ubuntu-latest"]

        :stability: experimental
        :description: Defines a target Runner by labels
        :throws: {Error} if both ``runsOn`` and ``runsOnGroup`` are specified
        '''
        result = self._values.get("workflow_runs_on")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def workflow_runs_on_group(self) -> typing.Optional[_GroupRunnerOptions_148c59c1]:
        '''(experimental) Github Runner Group selection options.

        :stability: experimental
        :description: Defines a target Runner Group by name and/or labels
        :throws: {Error} if both ``runsOn`` and ``runsOnGroup`` are specified
        '''
        result = self._values.get("workflow_runs_on_group")
        return typing.cast(typing.Optional[_GroupRunnerOptions_148c59c1], result)

    @builtins.property
    def default_release_branch(self) -> builtins.str:
        '''(experimental) The name of the main release branch.

        :default: "main"

        :stability: experimental
        '''
        result = self._values.get("default_release_branch")
        assert result is not None, "Required property 'default_release_branch' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def artifacts_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) A directory which will contain build artifacts.

        :default: "dist"

        :stability: experimental
        '''
        result = self._values.get("artifacts_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auto_approve_upgrades(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically approve deps upgrade PRs, allowing them to be merged by mergify (if configued).

        Throw if set to true but ``autoApproveOptions`` are not defined.

        :default: - true

        :stability: experimental
        '''
        result = self._values.get("auto_approve_upgrades")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def biome(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup Biome.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("biome")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def biome_options(self) -> typing.Optional[_BiomeOptions_452ab984]:
        '''(experimental) Biome options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("biome_options")
        return typing.cast(typing.Optional[_BiomeOptions_452ab984], result)

    @builtins.property
    def build_workflow(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define a GitHub workflow for building PRs.

        :default: - true if not a subproject

        :stability: experimental
        '''
        result = self._values.get("build_workflow")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def build_workflow_options(self) -> typing.Optional[_BuildWorkflowOptions_b756f97f]:
        '''(experimental) Options for PR build workflow.

        :stability: experimental
        '''
        result = self._values.get("build_workflow_options")
        return typing.cast(typing.Optional[_BuildWorkflowOptions_b756f97f], result)

    @builtins.property
    def build_workflow_triggers(self) -> typing.Optional[_Triggers_e9ae7617]:
        '''(deprecated) Build workflow triggers.

        :default: "{ pullRequest: {}, workflowDispatch: {} }"

        :deprecated: - Use ``buildWorkflowOptions.workflowTriggers``

        :stability: deprecated
        '''
        result = self._values.get("build_workflow_triggers")
        return typing.cast(typing.Optional[_Triggers_e9ae7617], result)

    @builtins.property
    def bundler_options(self) -> typing.Optional[_BundlerOptions_d60b85ed]:
        '''(experimental) Options for ``Bundler``.

        :stability: experimental
        '''
        result = self._values.get("bundler_options")
        return typing.cast(typing.Optional[_BundlerOptions_d60b85ed], result)

    @builtins.property
    def check_licenses(self) -> typing.Optional[_LicenseCheckerOptions_80bcd362]:
        '''(experimental) Configure which licenses should be deemed acceptable for use by dependencies.

        This setting will cause the build to fail, if any prohibited or not allowed licenses ares encountered.

        :default: - no license checks are run during the build and all licenses will be accepted

        :stability: experimental
        '''
        result = self._values.get("check_licenses")
        return typing.cast(typing.Optional[_LicenseCheckerOptions_80bcd362], result)

    @builtins.property
    def code_cov(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Define a GitHub workflow step for sending code coverage metrics to https://codecov.io/ Uses codecov/codecov-action@v5 By default, OIDC auth is used. Alternatively a token can be provided via ``codeCovTokenSecret``.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("code_cov")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def code_cov_token_secret(self) -> typing.Optional[builtins.str]:
        '''(experimental) Define the secret name for a specified https://codecov.io/ token.

        :default: - OIDC auth is used

        :stability: experimental
        '''
        result = self._values.get("code_cov_token_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def copyright_owner(self) -> typing.Optional[builtins.str]:
        '''(experimental) License copyright owner.

        :default: - defaults to the value of authorName or "" if ``authorName`` is undefined.

        :stability: experimental
        '''
        result = self._values.get("copyright_owner")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def copyright_period(self) -> typing.Optional[builtins.str]:
        '''(experimental) The copyright years to put in the LICENSE file.

        :default: - current year

        :stability: experimental
        '''
        result = self._values.get("copyright_period")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dependabot(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use dependabot to handle dependency upgrades.

        Cannot be used in conjunction with ``depsUpgrade``.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("dependabot")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def dependabot_options(self) -> typing.Optional[_DependabotOptions_0cedc635]:
        '''(experimental) Options for dependabot.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("dependabot_options")
        return typing.cast(typing.Optional[_DependabotOptions_0cedc635], result)

    @builtins.property
    def deps_upgrade(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use tasks and github workflows to handle dependency upgrades.

        Cannot be used in conjunction with ``dependabot``.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("deps_upgrade")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def deps_upgrade_options(
        self,
    ) -> typing.Optional[_UpgradeDependenciesOptions_1d8ce4da]:
        '''(experimental) Options for ``UpgradeDependencies``.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("deps_upgrade_options")
        return typing.cast(typing.Optional[_UpgradeDependenciesOptions_1d8ce4da], result)

    @builtins.property
    def gitignore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) Additional entries to .gitignore.

        :stability: experimental
        '''
        result = self._values.get("gitignore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def jest(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup jest unit tests.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("jest")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def jest_options(self) -> typing.Optional[_JestOptions_a085f64e]:
        '''(experimental) Jest options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("jest_options")
        return typing.cast(typing.Optional[_JestOptions_a085f64e], result)

    @builtins.property
    def mutable_build(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) Automatically update files modified during builds to pull-request branches.

        This means
        that any files synthesized by projen or e.g. test snapshots will always be up-to-date
        before a PR is merged.

        Implies that PR builds do not have anti-tamper checks.

        :default: true

        :deprecated: - Use ``buildWorkflowOptions.mutableBuild``

        :stability: deprecated
        '''
        result = self._values.get("mutable_build")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npmignore(self) -> typing.Optional[typing.List[builtins.str]]:
        '''(deprecated) Additional entries to .npmignore.

        :deprecated: - use ``project.addPackageIgnore``

        :stability: deprecated
        '''
        result = self._values.get("npmignore")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def npmignore_enabled(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Defines an .npmignore file. Normally this is only needed for libraries that are packaged as tarballs.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("npmignore_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def npm_ignore_options(self) -> typing.Optional[_IgnoreFileOptions_86c48b91]:
        '''(experimental) Configuration options for .npmignore file.

        :stability: experimental
        '''
        result = self._values.get("npm_ignore_options")
        return typing.cast(typing.Optional[_IgnoreFileOptions_86c48b91], result)

    @builtins.property
    def package(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Defines a ``package`` task that will produce an npm tarball under the artifacts directory (e.g. ``dist``).

        :default: true

        :stability: experimental
        '''
        result = self._values.get("package")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def prettier(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup prettier.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("prettier")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def prettier_options(self) -> typing.Optional[_PrettierOptions_41a5f203]:
        '''(experimental) Prettier options.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("prettier_options")
        return typing.cast(typing.Optional[_PrettierOptions_41a5f203], result)

    @builtins.property
    def projen_dev_dependency(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Indicates of "projen" should be installed as a devDependency.

        :default: - true if not a subproject

        :stability: experimental
        '''
        result = self._values.get("projen_dev_dependency")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_js(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate (once) .projenrc.js (in JavaScript). Set to ``false`` in order to disable .projenrc.js generation.

        :default: - true if projenrcJson is false

        :stability: experimental
        '''
        result = self._values.get("projenrc_js")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_js_options(self) -> typing.Optional[_ProjenrcOptions_179dd39f]:
        '''(experimental) Options for .projenrc.js.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("projenrc_js_options")
        return typing.cast(typing.Optional[_ProjenrcOptions_179dd39f], result)

    @builtins.property
    def projen_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) Version of projen to install.

        :default: - Defaults to the latest version.

        :stability: experimental
        '''
        result = self._values.get("projen_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pull_request_template(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Include a GitHub pull request template.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("pull_request_template")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def pull_request_template_contents(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''(experimental) The contents of the pull request template.

        :default: - default content

        :stability: experimental
        '''
        result = self._values.get("pull_request_template_contents")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def release(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Add release management to this project.

        :default: - true (false for subprojects)

        :stability: experimental
        '''
        result = self._values.get("release")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_to_npm(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Automatically release to npm when new versions are introduced.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("release_to_npm")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def release_workflow(self) -> typing.Optional[builtins.bool]:
        '''(deprecated) DEPRECATED: renamed to ``release``.

        :default: - true if not a subproject

        :deprecated: see ``release``.

        :stability: deprecated
        '''
        result = self._values.get("release_workflow")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def workflow_bootstrap_steps(
        self,
    ) -> typing.Optional[typing.List[_JobStep_c3287c05]]:
        '''(experimental) Workflow steps to use in order to bootstrap this repo.

        :default: "yarn install --frozen-lockfile && yarn projen"

        :stability: experimental
        '''
        result = self._values.get("workflow_bootstrap_steps")
        return typing.cast(typing.Optional[typing.List[_JobStep_c3287c05]], result)

    @builtins.property
    def workflow_git_identity(self) -> typing.Optional[_GitIdentity_6effc3de]:
        '''(experimental) The git identity to use in workflows.

        :default: - default GitHub Actions user

        :stability: experimental
        '''
        result = self._values.get("workflow_git_identity")
        return typing.cast(typing.Optional[_GitIdentity_6effc3de], result)

    @builtins.property
    def workflow_node_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) The node version used in GitHub Actions workflows.

        Always use this option if your GitHub Actions workflows require a specific to run.

        :default: - ``minNodeVersion`` if set, otherwise ``lts/*``.

        :stability: experimental
        '''
        result = self._values.get("workflow_node_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workflow_package_cache(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Enable Node.js package cache in GitHub workflows.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("workflow_package_cache")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disable_tsconfig(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Do not generate a ``tsconfig.json`` file (used by jsii projects since tsconfig.json is generated by the jsii compiler).

        :default: false

        :stability: experimental
        '''
        result = self._values.get("disable_tsconfig")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disable_tsconfig_dev(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Do not generate a ``tsconfig.dev.json`` file.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("disable_tsconfig_dev")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def docgen(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Docgen by Typedoc.

        :default: false

        :stability: experimental
        '''
        result = self._values.get("docgen")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def docs_directory(self) -> typing.Optional[builtins.str]:
        '''(experimental) Docs directory.

        :default: "docs"

        :stability: experimental
        '''
        result = self._values.get("docs_directory")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def entrypoint_types(self) -> typing.Optional[builtins.str]:
        '''(experimental) The .d.ts file that includes the type declarations for this module.

        :default: - .d.ts file derived from the project's entrypoint (usually lib/index.d.ts)

        :stability: experimental
        '''
        result = self._values.get("entrypoint_types")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def eslint(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Setup eslint.

        :default: - true, unless biome is enabled

        :stability: experimental
        '''
        result = self._values.get("eslint")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def eslint_options(self) -> typing.Optional[_EslintOptions_824f60bb]:
        '''(experimental) Eslint options.

        :default: - opinionated default options

        :stability: experimental
        '''
        result = self._values.get("eslint_options")
        return typing.cast(typing.Optional[_EslintOptions_824f60bb], result)

    @builtins.property
    def libdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Typescript  artifacts output directory.

        :default: "lib"

        :stability: experimental
        '''
        result = self._values.get("libdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def projenrc_ts(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Use TypeScript for your projenrc file (``.projenrc.ts``).

        :default: false

        :stability: experimental
        :pjnew: true
        '''
        result = self._values.get("projenrc_ts")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def projenrc_ts_options(self) -> typing.Optional[ProjenrcOptions]:
        '''(experimental) Options for .projenrc.ts.

        :stability: experimental
        '''
        result = self._values.get("projenrc_ts_options")
        return typing.cast(typing.Optional[ProjenrcOptions], result)

    @builtins.property
    def sample_code(self) -> typing.Optional[builtins.bool]:
        '''(experimental) Generate one-time sample in ``src/`` and ``test/`` if there are no files there.

        :default: true

        :stability: experimental
        '''
        result = self._values.get("sample_code")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def srcdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Typescript sources directory.

        :default: "src"

        :stability: experimental
        '''
        result = self._values.get("srcdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def testdir(self) -> typing.Optional[builtins.str]:
        '''(experimental) Jest tests directory. Tests files should be named ``xxx.test.ts``.

        If this directory is under ``srcdir`` (e.g. ``src/test``, ``src/__tests__``),
        then tests are going to be compiled into ``lib/`` and executed as javascript.
        If the test directory is outside of ``src``, then we configure jest to
        compile the code in-memory.

        :default: "test"

        :stability: experimental
        '''
        result = self._values.get("testdir")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tsconfig(self) -> typing.Optional[_TypescriptConfigOptions_8c5492cd]:
        '''(experimental) Custom TSConfig.

        :default: - default options

        :stability: experimental
        '''
        result = self._values.get("tsconfig")
        return typing.cast(typing.Optional[_TypescriptConfigOptions_8c5492cd], result)

    @builtins.property
    def tsconfig_dev(self) -> typing.Optional[_TypescriptConfigOptions_8c5492cd]:
        '''(experimental) Custom tsconfig options for the development tsconfig.json file (used for testing).

        :default: - use the production tsconfig options

        :stability: experimental
        '''
        result = self._values.get("tsconfig_dev")
        return typing.cast(typing.Optional[_TypescriptConfigOptions_8c5492cd], result)

    @builtins.property
    def tsconfig_dev_file(self) -> typing.Optional[builtins.str]:
        '''(experimental) The name of the development tsconfig.json file.

        :default: "tsconfig.dev.json"

        :stability: experimental
        '''
        result = self._values.get("tsconfig_dev_file")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ts_jest_options(self) -> typing.Optional[TsJestOptions]:
        '''(experimental) Options for ts-jest.

        :stability: experimental
        '''
        result = self._values.get("ts_jest_options")
        return typing.cast(typing.Optional[TsJestOptions], result)

    @builtins.property
    def typescript_version(self) -> typing.Optional[builtins.str]:
        '''(experimental) TypeScript version to use.

        NOTE: Typescript is not semantically versioned and should remain on the
        same minor, so we recommend using a ``~`` dependency (e.g. ``~1.2.3``).

        :default: "latest"

        :stability: experimental
        '''
        result = self._values.get("typescript_version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TypeScriptLibraryProjectOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Projenrc",
    "ProjenrcOptions",
    "ProjenrcTs",
    "ProjenrcTsOptions",
    "TsJestBabelConfig",
    "TsJestDiagnostics",
    "TsJestOptions",
    "TsJestTransformOptions",
    "TsJestTsconfig",
    "TypeScriptAppProject",
    "TypeScriptLibraryProject",
    "TypeScriptLibraryProjectOptions",
    "TypeScriptProject",
    "TypeScriptProjectOptions",
    "TypedocDocgen",
]

publication.publish()

def _typecheckingstub__2263ee9c745ea47c774563d843521472e79762041f4e1ae7ba448b00eb619b8d(
    project: TypeScriptProject,
    *,
    filename: typing.Optional[builtins.str] = None,
    projen_code_dir: typing.Optional[builtins.str] = None,
    swc: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c19ece862a34d563e3af49bcb2633dab3ba4ac5f67cc57c6fff86d7cca41defc(
    *,
    filename: typing.Optional[builtins.str] = None,
    projen_code_dir: typing.Optional[builtins.str] = None,
    swc: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f8247bfab52de99210dd1174bf8292517bfb90aa0435a94a64a093bcdcceb1d3(
    project: _Project_57d89203,
    *,
    filename: typing.Optional[builtins.str] = None,
    projen_code_dir: typing.Optional[builtins.str] = None,
    tsconfig_file_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__160fd3491644df95d187ac5907c3e3cc1eb206baf5e8a1cbfca8496701ab6df6(
    *,
    filename: typing.Optional[builtins.str] = None,
    projen_code_dir: typing.Optional[builtins.str] = None,
    tsconfig_file_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__57c74312f3b84d4697a7e445fdef068f4807b51470030ba0ac243d70498c8bca(
    config: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa38b428b489eb4f2e5ab1fa56039a74d05152687403b422fe16578573506d72(
    file_path: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__abb08ee9151f9ffaafab18cc1dd48f6143d5328362bb1f2c80aa95d395bbde58(
    config: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8c225926587b822ce73ff151cc8d04de0c607d2d0315e5c10b19bf90177fe777(
    *,
    transform_options: typing.Optional[typing.Union[TsJestTransformOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    transform_pattern: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1dea54f53ed685b6629951d7aaee8ae0563b656a849a1c5f2cf70786f2333cb1(
    *,
    ast_transformers: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    babel_config: typing.Optional[TsJestBabelConfig] = None,
    compiler: typing.Optional[builtins.str] = None,
    diagnostics: typing.Optional[TsJestDiagnostics] = None,
    isolated_modules: typing.Optional[builtins.bool] = None,
    stringify_content_path_regex: typing.Optional[builtins.str] = None,
    tsconfig: typing.Optional[TsJestTsconfig] = None,
    use_esm: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92dd15c4a7cabe98b93189ec1f931bb163c5658476fc9627211024b208dcbf8f(
    file_path: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a914f27f5d915b07b8847d407b03b08cab2aad7b213973084a9026526734c711(
    *,
    name: builtins.str,
    commit_generated: typing.Optional[builtins.bool] = None,
    git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
    git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
    logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
    outdir: typing.Optional[builtins.str] = None,
    parent: typing.Optional[_Project_57d89203] = None,
    projen_command: typing.Optional[builtins.str] = None,
    projenrc_json: typing.Optional[builtins.bool] = None,
    projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
    renovatebot: typing.Optional[builtins.bool] = None,
    renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_merge: typing.Optional[builtins.bool] = None,
    auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
    clobber: typing.Optional[builtins.bool] = None,
    dev_container: typing.Optional[builtins.bool] = None,
    github: typing.Optional[builtins.bool] = None,
    github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
    gitpod: typing.Optional[builtins.bool] = None,
    mergify: typing.Optional[builtins.bool] = None,
    mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
    project_type: typing.Optional[_ProjectType_fd80c725] = None,
    projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
    projen_token_secret: typing.Optional[builtins.str] = None,
    readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
    stale: typing.Optional[builtins.bool] = None,
    stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
    vscode: typing.Optional[builtins.bool] = None,
    allow_library_dependencies: typing.Optional[builtins.bool] = None,
    author_email: typing.Optional[builtins.str] = None,
    author_name: typing.Optional[builtins.str] = None,
    author_organization: typing.Optional[builtins.bool] = None,
    author_url: typing.Optional[builtins.str] = None,
    auto_detect_bin: typing.Optional[builtins.bool] = None,
    bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    bugs_email: typing.Optional[builtins.str] = None,
    bugs_url: typing.Optional[builtins.str] = None,
    bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    bun_version: typing.Optional[builtins.str] = None,
    code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
    deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    entrypoint: typing.Optional[builtins.str] = None,
    homepage: typing.Optional[builtins.str] = None,
    keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
    license: typing.Optional[builtins.str] = None,
    licensed: typing.Optional[builtins.bool] = None,
    max_node_version: typing.Optional[builtins.str] = None,
    min_node_version: typing.Optional[builtins.str] = None,
    npm_access: typing.Optional[_NpmAccess_134fa228] = None,
    npm_provenance: typing.Optional[builtins.bool] = None,
    npm_registry: typing.Optional[builtins.str] = None,
    npm_registry_url: typing.Optional[builtins.str] = None,
    npm_token_secret: typing.Optional[builtins.str] = None,
    npm_trusted_publishing: typing.Optional[builtins.bool] = None,
    package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
    package_name: typing.Optional[builtins.str] = None,
    peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
    peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    pnpm_version: typing.Optional[builtins.str] = None,
    repository: typing.Optional[builtins.str] = None,
    repository_directory: typing.Optional[builtins.str] = None,
    scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
    scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    stability: typing.Optional[builtins.str] = None,
    yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
    bump_package: typing.Optional[builtins.str] = None,
    jsii_release_version: typing.Optional[builtins.str] = None,
    major_version: typing.Optional[jsii.Number] = None,
    min_major_version: typing.Optional[jsii.Number] = None,
    next_version_command: typing.Optional[builtins.str] = None,
    npm_dist_tag: typing.Optional[builtins.str] = None,
    post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    prerelease: typing.Optional[builtins.str] = None,
    publish_dry_run: typing.Optional[builtins.bool] = None,
    publish_tasks: typing.Optional[builtins.bool] = None,
    releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
    release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
    release_environment: typing.Optional[builtins.str] = None,
    release_every_commit: typing.Optional[builtins.bool] = None,
    release_failure_issue: typing.Optional[builtins.bool] = None,
    release_failure_issue_label: typing.Optional[builtins.str] = None,
    release_schedule: typing.Optional[builtins.str] = None,
    release_tag_prefix: typing.Optional[builtins.str] = None,
    release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
    release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    release_workflow_name: typing.Optional[builtins.str] = None,
    release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    workflow_container_image: typing.Optional[builtins.str] = None,
    workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
    workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
    default_release_branch: builtins.str,
    artifacts_directory: typing.Optional[builtins.str] = None,
    auto_approve_upgrades: typing.Optional[builtins.bool] = None,
    biome: typing.Optional[builtins.bool] = None,
    biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
    build_workflow: typing.Optional[builtins.bool] = None,
    build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
    build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
    bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
    check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
    code_cov: typing.Optional[builtins.bool] = None,
    code_cov_token_secret: typing.Optional[builtins.str] = None,
    copyright_owner: typing.Optional[builtins.str] = None,
    copyright_period: typing.Optional[builtins.str] = None,
    dependabot: typing.Optional[builtins.bool] = None,
    dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
    deps_upgrade: typing.Optional[builtins.bool] = None,
    deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
    gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
    jest: typing.Optional[builtins.bool] = None,
    jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
    mutable_build: typing.Optional[builtins.bool] = None,
    npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
    npmignore_enabled: typing.Optional[builtins.bool] = None,
    npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
    package: typing.Optional[builtins.bool] = None,
    prettier: typing.Optional[builtins.bool] = None,
    prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
    projen_dev_dependency: typing.Optional[builtins.bool] = None,
    projenrc_js: typing.Optional[builtins.bool] = None,
    projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
    projen_version: typing.Optional[builtins.str] = None,
    pull_request_template: typing.Optional[builtins.bool] = None,
    pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
    release: typing.Optional[builtins.bool] = None,
    release_to_npm: typing.Optional[builtins.bool] = None,
    release_workflow: typing.Optional[builtins.bool] = None,
    workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
    workflow_node_version: typing.Optional[builtins.str] = None,
    workflow_package_cache: typing.Optional[builtins.bool] = None,
    disable_tsconfig: typing.Optional[builtins.bool] = None,
    disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
    docgen: typing.Optional[builtins.bool] = None,
    docs_directory: typing.Optional[builtins.str] = None,
    entrypoint_types: typing.Optional[builtins.str] = None,
    eslint: typing.Optional[builtins.bool] = None,
    eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
    libdir: typing.Optional[builtins.str] = None,
    projenrc_ts: typing.Optional[builtins.bool] = None,
    projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    sample_code: typing.Optional[builtins.bool] = None,
    srcdir: typing.Optional[builtins.str] = None,
    testdir: typing.Optional[builtins.str] = None,
    tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
    tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
    tsconfig_dev_file: typing.Optional[builtins.str] = None,
    ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    typescript_version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__05c2a64cbf1d03e81be8fd637cc486671fa9c1ee8abae939265da1f9e27dcc63(
    project: TypeScriptProject,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ac162883b4ecfe9863890d69bffa76d7f9ce16e619c94b9b2a4b7b8f222c3227(
    *,
    name: builtins.str,
    commit_generated: typing.Optional[builtins.bool] = None,
    git_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
    git_options: typing.Optional[typing.Union[_GitOptions_a65916a3, typing.Dict[builtins.str, typing.Any]]] = None,
    logging: typing.Optional[typing.Union[_LoggerOptions_eb0f6309, typing.Dict[builtins.str, typing.Any]]] = None,
    outdir: typing.Optional[builtins.str] = None,
    parent: typing.Optional[_Project_57d89203] = None,
    projen_command: typing.Optional[builtins.str] = None,
    projenrc_json: typing.Optional[builtins.bool] = None,
    projenrc_json_options: typing.Optional[typing.Union[_ProjenrcJsonOptions_9c40dd4f, typing.Dict[builtins.str, typing.Any]]] = None,
    renovatebot: typing.Optional[builtins.bool] = None,
    renovatebot_options: typing.Optional[typing.Union[_RenovatebotOptions_18e6b8a1, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_approve_options: typing.Optional[typing.Union[_AutoApproveOptions_dac86cbe, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_merge: typing.Optional[builtins.bool] = None,
    auto_merge_options: typing.Optional[typing.Union[_AutoMergeOptions_d112cd3c, typing.Dict[builtins.str, typing.Any]]] = None,
    clobber: typing.Optional[builtins.bool] = None,
    dev_container: typing.Optional[builtins.bool] = None,
    github: typing.Optional[builtins.bool] = None,
    github_options: typing.Optional[typing.Union[_GitHubOptions_21553699, typing.Dict[builtins.str, typing.Any]]] = None,
    gitpod: typing.Optional[builtins.bool] = None,
    mergify: typing.Optional[builtins.bool] = None,
    mergify_options: typing.Optional[typing.Union[_MergifyOptions_a6faaab3, typing.Dict[builtins.str, typing.Any]]] = None,
    project_type: typing.Optional[_ProjectType_fd80c725] = None,
    projen_credentials: typing.Optional[_GithubCredentials_ae257072] = None,
    projen_token_secret: typing.Optional[builtins.str] = None,
    readme: typing.Optional[typing.Union[_SampleReadmeProps_3518b03b, typing.Dict[builtins.str, typing.Any]]] = None,
    stale: typing.Optional[builtins.bool] = None,
    stale_options: typing.Optional[typing.Union[_StaleOptions_929db764, typing.Dict[builtins.str, typing.Any]]] = None,
    vscode: typing.Optional[builtins.bool] = None,
    allow_library_dependencies: typing.Optional[builtins.bool] = None,
    author_email: typing.Optional[builtins.str] = None,
    author_name: typing.Optional[builtins.str] = None,
    author_organization: typing.Optional[builtins.bool] = None,
    author_url: typing.Optional[builtins.str] = None,
    auto_detect_bin: typing.Optional[builtins.bool] = None,
    bin: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    bugs_email: typing.Optional[builtins.str] = None,
    bugs_url: typing.Optional[builtins.str] = None,
    bundled_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    bun_version: typing.Optional[builtins.str] = None,
    code_artifact_options: typing.Optional[typing.Union[_CodeArtifactOptions_e4782b3e, typing.Dict[builtins.str, typing.Any]]] = None,
    deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    dev_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    entrypoint: typing.Optional[builtins.str] = None,
    homepage: typing.Optional[builtins.str] = None,
    keywords: typing.Optional[typing.Sequence[builtins.str]] = None,
    license: typing.Optional[builtins.str] = None,
    licensed: typing.Optional[builtins.bool] = None,
    max_node_version: typing.Optional[builtins.str] = None,
    min_node_version: typing.Optional[builtins.str] = None,
    npm_access: typing.Optional[_NpmAccess_134fa228] = None,
    npm_provenance: typing.Optional[builtins.bool] = None,
    npm_registry: typing.Optional[builtins.str] = None,
    npm_registry_url: typing.Optional[builtins.str] = None,
    npm_token_secret: typing.Optional[builtins.str] = None,
    npm_trusted_publishing: typing.Optional[builtins.bool] = None,
    package_manager: typing.Optional[_NodePackageManager_3eb53bf6] = None,
    package_name: typing.Optional[builtins.str] = None,
    peer_dependency_options: typing.Optional[typing.Union[_PeerDependencyOptions_99d7d493, typing.Dict[builtins.str, typing.Any]]] = None,
    peer_deps: typing.Optional[typing.Sequence[builtins.str]] = None,
    pnpm_version: typing.Optional[builtins.str] = None,
    repository: typing.Optional[builtins.str] = None,
    repository_directory: typing.Optional[builtins.str] = None,
    scoped_packages_options: typing.Optional[typing.Sequence[typing.Union[_ScopedPackagesOptions_52f0a477, typing.Dict[builtins.str, typing.Any]]]] = None,
    scripts: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    stability: typing.Optional[builtins.str] = None,
    yarn_berry_options: typing.Optional[typing.Union[_YarnBerryOptions_b6942539, typing.Dict[builtins.str, typing.Any]]] = None,
    bump_package: typing.Optional[builtins.str] = None,
    jsii_release_version: typing.Optional[builtins.str] = None,
    major_version: typing.Optional[jsii.Number] = None,
    min_major_version: typing.Optional[jsii.Number] = None,
    next_version_command: typing.Optional[builtins.str] = None,
    npm_dist_tag: typing.Optional[builtins.str] = None,
    post_build_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    prerelease: typing.Optional[builtins.str] = None,
    publish_dry_run: typing.Optional[builtins.bool] = None,
    publish_tasks: typing.Optional[builtins.bool] = None,
    releasable_commits: typing.Optional[_ReleasableCommits_d481ce10] = None,
    release_branches: typing.Optional[typing.Mapping[builtins.str, typing.Union[_BranchOptions_13663d08, typing.Dict[builtins.str, typing.Any]]]] = None,
    release_environment: typing.Optional[builtins.str] = None,
    release_every_commit: typing.Optional[builtins.bool] = None,
    release_failure_issue: typing.Optional[builtins.bool] = None,
    release_failure_issue_label: typing.Optional[builtins.str] = None,
    release_schedule: typing.Optional[builtins.str] = None,
    release_tag_prefix: typing.Optional[builtins.str] = None,
    release_trigger: typing.Optional[_ReleaseTrigger_e4dc221f] = None,
    release_workflow_env: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    release_workflow_name: typing.Optional[builtins.str] = None,
    release_workflow_setup_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    versionrc_options: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    workflow_container_image: typing.Optional[builtins.str] = None,
    workflow_runs_on: typing.Optional[typing.Sequence[builtins.str]] = None,
    workflow_runs_on_group: typing.Optional[typing.Union[_GroupRunnerOptions_148c59c1, typing.Dict[builtins.str, typing.Any]]] = None,
    default_release_branch: builtins.str,
    artifacts_directory: typing.Optional[builtins.str] = None,
    auto_approve_upgrades: typing.Optional[builtins.bool] = None,
    biome: typing.Optional[builtins.bool] = None,
    biome_options: typing.Optional[typing.Union[_BiomeOptions_452ab984, typing.Dict[builtins.str, typing.Any]]] = None,
    build_workflow: typing.Optional[builtins.bool] = None,
    build_workflow_options: typing.Optional[typing.Union[_BuildWorkflowOptions_b756f97f, typing.Dict[builtins.str, typing.Any]]] = None,
    build_workflow_triggers: typing.Optional[typing.Union[_Triggers_e9ae7617, typing.Dict[builtins.str, typing.Any]]] = None,
    bundler_options: typing.Optional[typing.Union[_BundlerOptions_d60b85ed, typing.Dict[builtins.str, typing.Any]]] = None,
    check_licenses: typing.Optional[typing.Union[_LicenseCheckerOptions_80bcd362, typing.Dict[builtins.str, typing.Any]]] = None,
    code_cov: typing.Optional[builtins.bool] = None,
    code_cov_token_secret: typing.Optional[builtins.str] = None,
    copyright_owner: typing.Optional[builtins.str] = None,
    copyright_period: typing.Optional[builtins.str] = None,
    dependabot: typing.Optional[builtins.bool] = None,
    dependabot_options: typing.Optional[typing.Union[_DependabotOptions_0cedc635, typing.Dict[builtins.str, typing.Any]]] = None,
    deps_upgrade: typing.Optional[builtins.bool] = None,
    deps_upgrade_options: typing.Optional[typing.Union[_UpgradeDependenciesOptions_1d8ce4da, typing.Dict[builtins.str, typing.Any]]] = None,
    gitignore: typing.Optional[typing.Sequence[builtins.str]] = None,
    jest: typing.Optional[builtins.bool] = None,
    jest_options: typing.Optional[typing.Union[_JestOptions_a085f64e, typing.Dict[builtins.str, typing.Any]]] = None,
    mutable_build: typing.Optional[builtins.bool] = None,
    npmignore: typing.Optional[typing.Sequence[builtins.str]] = None,
    npmignore_enabled: typing.Optional[builtins.bool] = None,
    npm_ignore_options: typing.Optional[typing.Union[_IgnoreFileOptions_86c48b91, typing.Dict[builtins.str, typing.Any]]] = None,
    package: typing.Optional[builtins.bool] = None,
    prettier: typing.Optional[builtins.bool] = None,
    prettier_options: typing.Optional[typing.Union[_PrettierOptions_41a5f203, typing.Dict[builtins.str, typing.Any]]] = None,
    projen_dev_dependency: typing.Optional[builtins.bool] = None,
    projenrc_js: typing.Optional[builtins.bool] = None,
    projenrc_js_options: typing.Optional[typing.Union[_ProjenrcOptions_179dd39f, typing.Dict[builtins.str, typing.Any]]] = None,
    projen_version: typing.Optional[builtins.str] = None,
    pull_request_template: typing.Optional[builtins.bool] = None,
    pull_request_template_contents: typing.Optional[typing.Sequence[builtins.str]] = None,
    release: typing.Optional[builtins.bool] = None,
    release_to_npm: typing.Optional[builtins.bool] = None,
    release_workflow: typing.Optional[builtins.bool] = None,
    workflow_bootstrap_steps: typing.Optional[typing.Sequence[typing.Union[_JobStep_c3287c05, typing.Dict[builtins.str, typing.Any]]]] = None,
    workflow_git_identity: typing.Optional[typing.Union[_GitIdentity_6effc3de, typing.Dict[builtins.str, typing.Any]]] = None,
    workflow_node_version: typing.Optional[builtins.str] = None,
    workflow_package_cache: typing.Optional[builtins.bool] = None,
    disable_tsconfig: typing.Optional[builtins.bool] = None,
    disable_tsconfig_dev: typing.Optional[builtins.bool] = None,
    docgen: typing.Optional[builtins.bool] = None,
    docs_directory: typing.Optional[builtins.str] = None,
    entrypoint_types: typing.Optional[builtins.str] = None,
    eslint: typing.Optional[builtins.bool] = None,
    eslint_options: typing.Optional[typing.Union[_EslintOptions_824f60bb, typing.Dict[builtins.str, typing.Any]]] = None,
    libdir: typing.Optional[builtins.str] = None,
    projenrc_ts: typing.Optional[builtins.bool] = None,
    projenrc_ts_options: typing.Optional[typing.Union[ProjenrcOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    sample_code: typing.Optional[builtins.bool] = None,
    srcdir: typing.Optional[builtins.str] = None,
    testdir: typing.Optional[builtins.str] = None,
    tsconfig: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
    tsconfig_dev: typing.Optional[typing.Union[_TypescriptConfigOptions_8c5492cd, typing.Dict[builtins.str, typing.Any]]] = None,
    tsconfig_dev_file: typing.Optional[builtins.str] = None,
    ts_jest_options: typing.Optional[typing.Union[TsJestOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    typescript_version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
