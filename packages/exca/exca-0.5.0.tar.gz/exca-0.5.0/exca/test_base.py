# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import collections
import subprocess
import tempfile
import typing as tp
from pathlib import Path

import numpy as np
import pydantic
import pytest

from exca import ConfDict

from .map import MapInfra
from .task import TaskInfra
from .workdir import WorkDir


class Base(pydantic.BaseModel):
    infra: TaskInfra = TaskInfra(version="12")
    param: int = 12
    tag: str = "whatever"

    @infra.apply
    def func(self) -> int:
        return 2 * self.param


class SubInfra(Base):
    infra: TaskInfra = TaskInfra()


class SubFunc(Base):

    def func(self) -> int:
        return 3 * super().func()


class SubInfraFunc(Base):
    infra: TaskInfra = TaskInfra()

    @infra.apply(exclude_from_cache_uid=("tag",))
    def func(self) -> int:
        return 3 * super().func()


class SubInfra2Func(Base):
    infra2: TaskInfra = TaskInfra()

    @infra2.apply(exclude_from_cache_uid=("tag",))
    def func(self) -> int:
        return 3 * super().func()


class SubBase(Base):
    pass


# with map infra
class BaseMap(pydantic.BaseModel):
    infra: MapInfra = MapInfra(version="12")
    tag: str = "whatever"

    @infra.apply(item_uid=str)
    def func(self, inds: tp.Sequence[int]) -> tp.Iterator[float]:
        for ind in inds:
            yield ind * np.random.rand()


class SubMapInfra(BaseMap):
    infra: MapInfra = MapInfra(version="24")


def test_subclass_map_infra(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        _ = SubMapInfra(tag="hello", infra={"folder": tmp_path})  # type: ignore


def test_subclass_infra(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError):
        _ = SubInfra(param=13, tag="hello", infra={"folder": tmp_path})  # type: ignore


def test_subclass_func(tmp_path: Path) -> None:
    whatever = SubFunc(param=13, tag="hello", infra={"folder": tmp_path})  # type: ignore
    assert whatever.func() == 78
    names = [fp.name for fp in tmp_path.iterdir()]
    assert tuple("Base.func" in n for n in names) == (True,)


def test_subclass_infra_func(tmp_path: Path) -> None:
    whatever = SubInfraFunc(param=13, tag="hello", infra={"folder": tmp_path})  # type: ignore
    assert whatever.func() == 78
    names = [fp.name for fp in tmp_path.iterdir()]
    assert tuple("SubInfraFunc.func" in n for n in names) == (True,)


def test_subclass_infra2_func(tmp_path: Path) -> None:
    whatever = SubInfra2Func(param=13, tag="hello", infra={"folder": tmp_path}, infra2={"folder": tmp_path})  # type: ignore
    assert whatever.func() == 78
    names = sorted(fp.name for fp in tmp_path.iterdir())
    assert tuple("SubInfra2Func.func" in n for n in names) == (False, True), names
    assert tuple("Base.func" in n for n in names) == (True, False), names


class BaseRaw(pydantic.BaseModel):
    # only derived, never used independently
    infra: TaskInfra = TaskInfra(version="12")
    param: int = 12
    tag: str = "whatever"

    @infra.apply
    def func(self) -> int:
        return 2 * self.param


class SubInfraFuncRaw(BaseRaw):
    infra: TaskInfra = TaskInfra()

    @infra.apply(exclude_from_cache_uid=("tag",))
    def func(self) -> int:
        return 3 * super().func()


def test_subclass_infra_func_raw(tmp_path: Path) -> None:
    whatever = SubInfraFuncRaw(param=13, tag="hello", infra={"folder": tmp_path})  # type: ignore
    assert whatever.func() == 78
    names = [fp.name for fp in tmp_path.iterdir()]
    assert tuple("SubInfraFuncRaw.func" in n for n in names) == (True,)


@pytest.mark.parametrize(
    "cls,name",
    [
        (Base, "Base.func,12"),
        (SubFunc, "Base.func,12"),  # function is overriden
        (SubInfra2Func, "Base.func,12"),  # function is overriden
        (SubBase, "SubBase.func,12"),  # function is the same -> get new class
    ],
)
def test_cache_names(cls: tp.Type[Base], name: str, tmp_path: Path) -> None:
    base = Base.__module__ + "."  # <...>.test_base
    whatever = cls(infra={"folder": tmp_path})  # type: ignore
    assert whatever.infra.uid() == base + name + "/default"


# END OF SUBCLASSING TEST


class MyCfg(pydantic.BaseModel):
    infra: TaskInfra = TaskInfra(gpus_per_node=12)
    param: int = 12
    other: int = 12

    def exclude(self) -> tp.Tuple[str]:
        return ("other",)

    @infra.apply(exclude_from_cache_uid=exclude)
    def func(self) -> np.ndarray:
        return np.random.rand(3, 4)


class MyCfg2(MyCfg):
    infra: TaskInfra = TaskInfra(gpus_per_node=12)

    @infra.apply(exclude_from_cache_uid="method:exclude")
    def func(self) -> np.ndarray:
        return np.random.rand(3, 4)


class MyCfg3(MyCfg):
    infra: TaskInfra = TaskInfra(gpus_per_node=12)

    @infra.apply(exclude_from_cache_uid="method:does_not_exist")
    def func(self) -> np.ndarray:
        return np.random.rand(3, 4)


@pytest.mark.parametrize("Cfg", (MyCfg, MyCfg2))
def test_exclude_func(tmp_path: Path, Cfg: tp.Type[MyCfg]) -> None:
    cfg = Cfg(infra={"folder": tmp_path})  # type: ignore
    cfgp = cfg.infra.clone_obj(param=13)
    cfgo = cfg.infra.clone_obj(other=13)
    np.testing.assert_array_equal(cfg.func(), cfgo.func())
    with pytest.raises(AssertionError):
        np.testing.assert_array_equal(cfg.func(), cfgp.func())


def test_exclude_func_errors() -> None:
    cfg = MyCfg3()
    with pytest.raises(RuntimeError):
        _ = cfg.infra.config()

    with pytest.raises(TypeError):

        # pylint: disable=unused-variable
        class MyCfg4(MyCfg):
            infra: TaskInfra = TaskInfra(gpus_per_node=12)

            @infra.apply(exclude_from_cache_uid="bad-format-string")
            def func(self) -> np.ndarray:
                return np.random.rand(3, 4)


def test_infra_default_propagation(tmp_path: Path) -> None:
    cfg = MyCfg(infra={"folder": tmp_path})  # type: ignore
    assert cfg.infra.gpus_per_node == 12


def test_uid_string() -> None:
    cfg = MyCfg()
    cfg.infra._uid_string = "blublu"
    with pytest.raises(ValueError):
        cfg.infra.uid()
    cfg.infra._uid_string = "{method}@{version}-{uid}"
    assert cfg.infra.uid().endswith("MyCfg.func@0-default")
    # also check equality
    assert cfg.infra == cfg.infra


def test_hidden_infra(tmp_path: Path) -> None:
    class Hidden(pydantic.BaseModel):
        _infra: TaskInfra = TaskInfra(folder=tmp_path)
        param: int = 12

        @_infra.apply
        def func(self) -> int:
            return 2 * self.param

    obj = Hidden(param=13)
    assert obj._infra is not Hidden._infra
    assert obj.func() == 26
    names = [fp.name for fp in tmp_path.iterdir()]
    assert tuple("Hidden.func" in n for n in names) == (True,), names


class Copied(pydantic.BaseModel):
    _infra: TaskInfra = TaskInfra()
    infra: TaskInfra = TaskInfra()
    param: int = 12

    def model_post_init(self, log__: tp.Any) -> None:
        super().model_post_init(log__)
        self._infra._update(self.infra)

    @infra.apply
    def func1(self) -> int:
        return self.param

    @_infra.apply
    def func2(self) -> int:
        return 2 * self.param


def test_copied_infra(tmp_path: Path) -> None:
    obj = Copied(param=13, infra={"folder": tmp_path})  # type: ignore
    assert obj._infra is not obj.infra
    assert obj.func1() == 13
    assert obj.func2() == 26
    names = [fp.name for fp in tmp_path.iterdir()]
    assert tuple("Copied.func" in n for n in names) == (True, True), names
    _ = obj.infra.clone_obj()


def test_changing_version(tmp_path: Path) -> None:
    class VersionXp(Base):
        infra: TaskInfra = TaskInfra(version="12")

        @infra.apply
        def func(self) -> int:
            return super().func()

    class Main(pydantic.BaseModel):
        xp: VersionXp = VersionXp()
        infra: TaskInfra = TaskInfra(version="1")

        def model_post_init(self, log__: tp.Any) -> None:
            super().model_post_init(log__)
            self.xp.infra.folder = self.infra.folder

        @infra.apply
        def func(self) -> int:
            return self.xp.func()

    m = Main(infra={"folder": tmp_path})  # type: ignore
    _ = m.func()
    assert ",12/" in m.xp.infra.uid()
    if not m.xp.infra.uid_folder().exists():  # type: ignore
        raise RuntimeError("Folder should have been created by m.func()")

    class VersionXp(Base):  # type: ignore
        infra: TaskInfra = TaskInfra(version="13")

        @infra.apply
        def func(self) -> int:
            return super().func()

    class Main(Main):  # type: ignore
        xp: VersionXp = VersionXp()

    m = Main(infra={"folder": tmp_path})  # type: ignore
    with pytest.raises(RuntimeError):
        _ = m.func()

    # sub-config should still work because folder is different
    assert ",13/" in m.xp.infra.uid()
    _ = m.xp.func()


class MissingInfra(pydantic.BaseModel):  # COMPATIBIILTY
    infra: TaskInfra
    infra2: TaskInfra = TaskInfra()

    @infra2.apply
    def run(self) -> None:
        return


def test_buggy_compat_validator(tmp_path: Path) -> None:
    _ = MissingInfra(infra={"folder": tmp_path})  # type: ignore


def test_infra_already_applied_obj() -> None:
    infra = TaskInfra(version="12")
    cfg1 = MyCfg(infra=infra)
    cfg2 = MyCfg(infra=infra)
    assert cfg2.infra is not cfg1.infra
    # test not applied infra
    with pytest.raises(RuntimeError):
        _ = infra.config()


class DoubleCfg(pydantic.BaseModel):  # COMPATIBIILTY
    infra: TaskInfra = TaskInfra()
    infra2: TaskInfra = TaskInfra()

    @infra.apply
    def func(self) -> int:
        return 12

    @infra2.apply
    def func2(self) -> int:
        return 13


def test_infra_already_applied_name() -> None:
    infra = TaskInfra(version="12")
    cfg = DoubleCfg(infra=infra, infra2=infra)
    assert cfg.infra is not cfg.infra2


def test_obj_infras() -> None:
    cfg = Copied()
    infras = cfg.infra.obj_infras()
    assert set(infras) == {"infra", "_infra"}
    assert infras["infra"] is cfg.infra


class Xp(pydantic.BaseModel):
    infra: TaskInfra = TaskInfra(version="12")
    base: Base = Base()

    @infra.apply
    def func(self) -> None:
        pass


def test_obj_in_obj() -> None:
    # triggered model_with_infra_validator_after error because obj already set
    base = Base()
    _ = Xp(base=base)


class WrappedBase(pydantic.BaseModel):
    xp: Base = Base()
    infra: TaskInfra = TaskInfra(version="12")

    @infra.apply
    def wfunc(self) -> int:
        return 12


def test_tricky_update(tmp_path: Path) -> None:
    # pb in confdict for subconfig
    infra: tp.Any = {
        "folder": tmp_path,
        "workdir": {"copied": [Path(__file__).parent], "includes": ("*.py",)},
    }
    xp = Base().infra.clone_obj(infra=infra)
    wxp = WrappedBase(xp=xp)
    wxp.infra._update(dict(xp.infra))
    wxp.infra._update(wxp.xp.infra.model_dump())
    assert isinstance(wxp.infra.workdir, WorkDir)
    wxp.infra._update(xp.infra)
    assert isinstance(wxp.infra.workdir, WorkDir)


def test_missing_base_model() -> None:
    with pytest.raises(RuntimeError):

        class MissingBaseModel:  # pylint: disable=unused-variable
            infra: TaskInfra = TaskInfra(version="12")


class WeirdTypes(pydantic.BaseModel):
    alphas: tp.List[float] = list(np.ones(2))
    infra: TaskInfra = TaskInfra()

    @infra.apply
    def build(self) -> int:
        return 8


class OrderedCfg(pydantic.BaseModel):
    d: collections.OrderedDict[str, tp.Any] = collections.OrderedDict()
    d2: dict[str, tp.Any] = {}
    infra: TaskInfra = TaskInfra()

    @infra.apply
    def build(self) -> str:
        return ",".join(self.d)


def test_ordered_dict(tmp_path: Path) -> None:
    keys = [str(k) for k in range(100)]
    whatever = OrderedCfg(d={k: 12 for k in keys}, infra={"folder": tmp_path})  # type: ignore
    assert isinstance(whatever.d, collections.OrderedDict)
    assert whatever.build() == ",".join(keys)
    # new reorder
    keys2 = list(keys)
    np.random.shuffle(keys2)
    whatever2 = OrderedCfg(d={k: 12 for k in keys2}, infra={"folder": tmp_path})  # type: ignore
    assert whatever2.build() == ",".join(keys2)
    # check yaml
    fp: Path = whatever2.infra.uid_folder() / "config.yaml"  # type: ignore
    cfg = ConfDict.from_yaml(fp)
    cfg["infra.mode"] = "read-only"
    whatever3 = OrderedCfg(**cfg)
    assert ",".join(whatever3.d) == ",".join(keys2)
    assert whatever3.build() == ",".join(keys2)
    # check modeldump/cloneobj
    whatever4 = whatever3.infra.clone_obj()
    assert ",".join(whatever4.d) == ",".join(whatever3.d)


def test_unordered_dict() -> None:
    ordered = OrderedCfg(d2=collections.OrderedDict({str(k): 12 for k in range(12)}))
    if isinstance(ordered.d2, collections.OrderedDict):
        raise AssertionError("OrderedDict should be cast to standard dict by pydantic")


class Num(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")
    k: int
    other: int = 12


class OrderedNumCfg(pydantic.BaseModel):
    d: collections.OrderedDict[str, Num] = collections.OrderedDict()
    infra: TaskInfra = TaskInfra()

    @infra.apply
    def build(self) -> str:
        return ",".join(self.d)


def test_ordered_dict_with_subcfg(tmp_path: Path) -> None:
    nums = OrderedNumCfg(d={"a": {"k": 12}}, infra={"folder": tmp_path})  # type: ignore
    _ = nums.build()
    uid = nums.infra.uid()
    assert "d={a.k=12}" in uid


def test_ordered_dict_with_subcfg_flat(tmp_path: Path) -> None:
    infra = {"folder": tmp_path}
    keys = list(range(10))
    np.random.shuffle(keys)
    nums = OrderedNumCfg(d={f"{k}": {"k": k, "other": 0} for k in keys}, infra=infra)  # type: ignore
    flat = nums.infra.config().flat()
    flat["d.5.k"] = 12
    nums2 = OrderedNumCfg(**ConfDict(flat))
    keys2 = [v.k for v in nums2.d.values()]
    np.testing.assert_equal([k if k != 5 else 12 for k in keys], keys2)


def test_clone_obj_with_dict(tmp_path: Path) -> None:
    keys = [str(k) for k in range(10)]
    w = OrderedCfg(d={k: [1] for k in keys}, infra={"folder": tmp_path})  # type: ignore
    w2 = w.infra.clone_obj()
    w2.d["0"][0] = 12
    assert w.d["0"][0] == 1


class OptCfg(OrderedNumCfg):
    num: Num | None = Num(k=12)


def test_clone_obj_with_optional_subconfig() -> None:
    cfg = OptCfg()
    assert cfg.num is not None
    assert cfg.num.k == 12
    nonecfg = cfg.infra.clone_obj({"num": None})
    assert nonecfg.num is None
    cfg2 = nonecfg.infra.clone_obj({"num": {"k": 10}})
    assert cfg2.num is not None
    assert cfg2.num.k == 10


def test_weird_types(tmp_path: Path) -> None:
    whatever = WeirdTypes(infra={"folder": tmp_path})  # type: ignore
    _ = whatever.build()


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")


class FrozenBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)


@pytest.mark.parametrize("PydanticBase", (BaseModel, FrozenBaseModel))
def test_large_frozen_model(
    tmp_path: Path, PydanticBase: tp.Type[pydantic.BaseModel]
) -> None:
    fields: dict[str, tp.Any] = {f"int{k}": (int, k) for k in range(5)}
    fields.update({f"str{k}": (str, str(k)) for k in range(5)})
    for level in range(12):
        Level = pydantic.create_model(f"Level{level}", **fields, __base__=PydanticBase)
        fields[f"level{level}"] = (Level, Level())

    class DeepH(PydanticBase):  # type: ignore
        x: Level = Level()  # type: ignore
        infra: TaskInfra = TaskInfra()

        @infra.apply
        def process(self) -> dict[str, tp.Any]:
            return self.infra.config().flat()

    # TODO: weirdly enough, model_dump (and therefore infra.config)
    # does not work in a local job, and returns an empty dict
    dh = DeepH(infra={"folder": tmp_path})
    array = []
    for k in range(10):  # instantiate several items just to check it works
        array.append(dh.infra.clone_obj({"x.int0": k}))
    out = array[0].process()
    assert len(out) > 10000
    assert isinstance(out, dict)


class BasicP(pydantic.BaseModel):
    b: pydantic.BaseModel | None = None
    infra: TaskInfra = TaskInfra(version="12")

    @infra.apply
    def func(self) -> int:
        return 12


def test_basic_pydantic(tmp_path: Path) -> None:
    _ = BasicP()


class Ambiguous(pydantic.BaseModel):
    float_or_list: float | list[float] = [0.0, 1.0]
    infra: TaskInfra = TaskInfra(version="12")

    @infra.apply
    def func(self) -> tp.Any:
        return self.float_or_list


def test_ambiguous_clone() -> None:
    a = Ambiguous()
    a.infra.clone_obj({"float_or_list": 12})


def test_defined_in_main() -> None:
    try:
        import neuralset as ns

        cwd = Path(ns.__file__).parents[1]
    except ImportError:
        import exca

        cwd = Path(exca.__file__).parents[1]
    path = Path(__file__).with_suffix("").relative_to(cwd)
    cmd = str(path).replace("/", ".")
    subprocess.check_call(f"python -m {cmd}".split(), shell=False, cwd=cwd)


if __name__ == "__main__":

    class MainCls(pydantic.BaseModel):
        infra: TaskInfra = TaskInfra(version="12")
        param: int = 12

        @infra.apply
        def func(self) -> int:
            return 2 * self.param

    with tempfile.TemporaryDirectory() as tmp:
        model_ = MainCls(param=13, infra={"folder": tmp, "cluster": "local"})  # type: ignore
        assert model_.func() == 26
        assert list(Path(tmp).iterdir())
