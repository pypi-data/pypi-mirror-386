# Pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε縺ｸ縺ｮ遘ｻ陦瑚ｨ育判

**菴懈・譌･:** 2025-10-03
**繧ｹ繝・・繧ｿ繧ｹ:** 謠先｡・**髢｢騾｣:** Root Structure Policy, Codex Review (tests/outputs/b20/phase4-testing/codex_review_report.md)

---

## 搭 繧ｨ繧ｰ繧ｼ繧ｯ繝・ぅ繝悶し繝槭Μ繝ｼ

迴ｾ蝨ｨ縺ｮ繝・せ繝医う繝ｳ繝輔Λ縺ｯ `tempfile.TemporaryDirectory()` 縺ｫ繧医ｋ謇句虚邂｡逅・→pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε縺梧ｷｷ蝨ｨ縺励※縺翫ｊ縲∽ｿ晏ｮ域ｧ縺ｨ繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・縺ｮ菫｡鬆ｼ諤ｧ縺ｫ隱ｲ鬘後′縺ゅｊ縺ｾ縺吶よ悽謠先｡医・縲・*pytest讓呎ｺ悶・ `tmp_path` / `tmp_path_factory` 縺ｸ縺ｮ谿ｵ髫守噪遘ｻ陦・*縺ｫ繧医ｊ縲√ユ繧ｹ繝医ョ繝ｼ繧ｿ邂｡逅・ｒ邨ｱ荳縺励∬・蜍輔け繝ｪ繝ｼ繝ｳ繧｢繝・・縺ｨ蜿ｯ隱ｭ諤ｧ繧貞髄荳翫＆縺帙∪縺吶・
**譛溷ｾ・柑譫・**
- 繝・せ繝医ョ繝ｼ繧ｿ縺ｮ閾ｪ蜍輔け繝ｪ繝ｼ繝ｳ繧｢繝・・・・00%菫晁ｨｼ・・- 繧ｳ繝ｼ繝峨・蜿ｯ隱ｭ諤ｧ蜷台ｸ奇ｼ・0%蜑頑ｸ幄ｦ玖ｾｼ縺ｿ・・- 繝ｫ繝ｼ繝医ョ繧｣繝ｬ繧ｯ繝医Μ豎壽沒繝ｪ繧ｹ繧ｯ縺ｮ螳悟・謗帝勁

---

## 識 閭梧勹縺ｨ隱ｲ鬘・
### 迴ｾ迥ｶ縺ｮ蝠城｡檎せ

#### 1. 繝・せ繝医ョ繝ｼ繧ｿ邂｡逅・・豺ｷ蝨ｨ

**蝠城｡・**
```python
# 繝代ち繝ｼ繝ｳ1: 謇句虚邂｡逅・(tempfile)
@pytest.fixture(scope="session")
def temp_project_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # 讒矩菴懈・...
        yield temp_path
    # 譏守､ｺ逧・↑繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・荳崎ｦ√□縺後√お繝ｩ繝ｼ譎ゅ・謖吝虚縺御ｸ埼乗・

# 繝代ち繝ｼ繝ｳ2: pytest讓呎ｺ・(tmp_path)
def test_something(tmp_path):
    test_file = tmp_path / "data.txt"
    # pytest縺瑚・蜍輔け繝ｪ繝ｼ繝ｳ繧｢繝・・

# 繝代ち繝ｼ繝ｳ3: 繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ (蝠城｡・
def get_management_dir(self):
    return project_root / "temp" / "test_data" / "50_邂｡逅・ｳ・侭"  # 謇句虚邂｡逅・```

**蠖ｱ髻ｿ:**
- 繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・縺ｮ荳雋ｫ諤ｧ谺螯・- 繝・せ繝亥､ｱ謨玲凾縺ｮ谿矩ｪｸ繝輔ぃ繧､繝ｫ
- 繝ｫ繝ｼ繝医ョ繧｣繝ｬ繧ｯ繝医Μ豎壽沒繝ｪ繧ｹ繧ｯ・・0_繝励Ο繝・ヨ/, 40_蜴溽ｨｿ/ 縺御ｽ懈・縺輔ｌ縺溷ｮ溽ｸｾ・・
#### 2. Codex繝ｬ繝薙Η繝ｼ縺ｧ縺ｮ謖・遭

**Codex Review Score:** 箝絶ｭ絶ｭ・(3/5) - "謾ｹ蝟・′蠢・ｦ・

> "pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε縺ｮ豢ｻ逕ｨ荳崎ｶｳ縲よ焔蜍慕ｮ｡逅・↓繧医ｊ菫晏ｮ域ｧ縺御ｽ惹ｸ九＠縺ｦ縺・ｋ縲・

**險ｼ霍｡:**
- `tests/conftest.py:233` - `tempfile.TemporaryDirectory()` 菴ｿ逕ｨ
- `tests/conftest.py:143-149` - `project_root / "temp/test_data/..."` 繝上・繝峨さ繝ｼ繝・- `tests/test_18step_async_performance.py:36` - 譛霑台ｿｮ豁｣縺励◆縺梧焔蜍慕ｮ｡逅・・縺ｾ縺ｾ

#### 3. Root Structure Policy驕募渚繝ｪ繧ｹ繧ｯ

**螳溽ｸｾ:**
- 2025-10-03: `20_繝励Ο繝・ヨ/`, `40_蜴溽ｨｿ/`, `50_邂｡逅・ｳ・侭/` 縺後Ν繝ｼ繝医↓菴懈・縺輔ｌ縺・- 蜴溷屏: `get_management_dir()` 縺後Ν繝ｼ繝育峩荳九・繝代せ繧定ｿ斐＠縺ｦ縺・◆
- 蟇ｾ蠢・ commit dd590ea5 縺ｧ `temp/test_data/` 驟堺ｸ九↓菫ｮ豁｣

**谿句ｭ倥Μ繧ｹ繧ｯ:**
- 謇句虚繝代せ邂｡逅・↓繧医ｊ縲∝ｰ・擂逧・↓蜷梧ｧ倥・蝠城｡後′蜀咲匱縺吶ｋ蜿ｯ閭ｽ諤ｧ

---

## 噫 謠先｡亥・螳ｹ

### 遘ｻ陦梧婿驥・
**蜴溷援:**
1. **譌｢蟄倥ユ繧ｹ繝医・蜍穂ｽ懊ｒ菫晁ｨｼ**・亥ｾ梧婿莠呈鋤諤ｧ邯ｭ謖・ｼ・2. **谿ｵ髫守噪縺ｪ遘ｻ陦・*・井ｸ諡ｬ螟画峩縺ｫ繧医ｋ豺ｷ荵ｱ繧貞屓驕ｿ・・3. **pytest讓呎ｺ悶∈縺ｮ螳悟・貅匁侠**・医・繧ｹ繝医・繝ｩ繧ｯ繝・ぅ繧ｹ驕ｩ逕ｨ・・
### 蟇ｾ雎｡繝輔ぃ繧､繝ｫ縺ｨ蜆ｪ蜈亥ｺｦ

| 繝輔ぃ繧､繝ｫ | 迴ｾ迥ｶ | 蟇ｾ蠢・| 蜆ｪ蜈亥ｺｦ |
|---------|------|------|--------|
| `tests/conftest.py` | `tempfile` + 繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ | `tmp_path_factory` 縺ｫ邨ｱ荳 | 閥 High |
| `tests/test_18step_async_performance.py` | `tempfile` 謇句虚邂｡逅・| `tmp_path` 蛻ｩ逕ｨ | 泯 Medium |
| `tests/unit/infrastructure/test_base.py` | `project_root / "temp/tests"` | `tmp_path` 蛻ｩ逕ｨ | 泯 Medium |
| 莉悶・邨ｱ蜷医・E2E繝・せ繝・| 豺ｷ蝨ｨ | 鬆・ｬ｡遘ｻ陦・| 泙 Low |

---

## 盗 螳溯｣・ｨ育判

### Phase 1: `conftest.py` 縺ｮ讓呎ｺ門喧・・igh Priority・・
#### 1.1 `temp_project_dir` 繝輔ぅ繧ｯ繧ｹ繝√Ε縺ｮ譖ｸ縺肴鋤縺・
**Before (迴ｾ迥ｶ):**
```python
@pytest.fixture(scope="session")
def temp_project_dir():
    """繝・せ繝育畑荳譎ゅョ繧｣繝ｬ繧ｯ繝医Μ(session繧ｹ繧ｳ繝ｼ繝・"""
    path_service = get_path_service()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # 讒矩菴懈・...
        yield temp_path
```

**After (謠先｡・:**
```python
@pytest.fixture(scope="session")
def temp_project_dir(tmp_path_factory):
    """繝・せ繝育畑荳譎ゅョ繧｣繝ｬ繧ｯ繝医Μ(session繧ｹ繧ｳ繝ｼ繝・

    pytest讓呎ｺ悶・ tmp_path_factory 繧剃ｽｿ逕ｨ縺励∬・蜍輔け繝ｪ繝ｼ繝ｳ繧｢繝・・繧剃ｿ晁ｨｼ縲・    """
    temp_path = tmp_path_factory.mktemp("noveler_test_project")
    path_service = get_path_service()

    # 蝓ｺ譛ｬ繝・ぅ繝ｬ繧ｯ繝医Μ讒矩繧剃ｽ懈・
    try:
        (temp_path / str(path_service.get_manuscript_dir())).mkdir(parents=True, exist_ok=True)
        (temp_path / str(path_service.get_management_dir())).mkdir(parents=True, exist_ok=True)
        (temp_path / str(path_service.get_plots_dir())).mkdir(parents=True, exist_ok=True)
        (temp_path / str(path_service.get_settings_dir())).mkdir(parents=True, exist_ok=True)
    except AttributeError:
        # 繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ逕ｨ繝・ぅ繝ｬ繧ｯ繝医Μ菴懈・
        manuscripts_path = get_test_manuscripts_path()
        (temp_path / manuscripts_path).mkdir(parents=True, exist_ok=True)
        (temp_path / "50_邂｡逅・ｳ・侭").mkdir(exist_ok=True)
        (temp_path / "50_邂｡逅・ｳ・侭" / "plots").mkdir(parents=True, exist_ok=True)
        (temp_path / "config").mkdir(exist_ok=True)

    # 霑ｽ蜉繝・ぅ繝ｬ繧ｯ繝医Μ
    (temp_path / "plots").mkdir(exist_ok=True)
    (temp_path / "quality").mkdir(exist_ok=True)

    # 繝励Ο繧ｸ繧ｧ繧ｯ繝郁ｨｭ螳壹ヵ繧｡繧､繝ｫ菴懈・
    project_config = {
        "project": {
            "title": "繝・せ繝医・繝ｭ繧ｸ繧ｧ繧ｯ繝・,
            "author": "繝・せ繝医Θ繝ｼ繧ｶ繝ｼ",
            "genre": "繝輔ぃ繝ｳ繧ｿ繧ｸ繝ｼ",
            "ncode": "N0000XX",
        },
    }
    with open(temp_path / "繝励Ο繧ｸ繧ｧ繧ｯ繝郁ｨｭ螳・yaml", "w", encoding="utf-8") as f:
        yaml.dump(project_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    yield temp_path
    # pytest 縺瑚・蜍慕噪縺ｫ繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・・域・遉ｺ逧・↑蜑企勁荳崎ｦ・ｼ・```

**螟画峩轤ｹ:**
- 笨・`tempfile.TemporaryDirectory()` 竊・`tmp_path_factory.mktemp()`
- 笨・context manager 荳崎ｦ・ｼ・ytest邂｡逅・ｼ・- 笨・繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・閾ｪ蜍募喧

#### 1.2 `FallbackPathService` 縺ｮ繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ蜑企勁

**Before (迴ｾ迥ｶ):**
```python
class FallbackPathService:
    def get_management_dir(self):
        return project_root / "temp" / "test_data" / "50_邂｡逅・ｳ・侭"  # 繝上・繝峨さ繝ｼ繝・
    def get_plots_dir(self):
        return project_root / "temp" / "test_data" / "50_邂｡逅・ｳ・侭" / "plots"
```

**After (謠先｡・:**
```python
@pytest.fixture(scope="session")
def get_path_service(tmp_path_factory):
    """繝代せ繧ｵ繝ｼ繝薙せ縺ｮ繝輔ぅ繧ｯ繧ｹ繝√Ε蛹・
    tmp_path_factory 繧呈ｳｨ蜈･縺励｝ytest邂｡逅・ｸ九・繝代せ繧定ｿ斐☆縲・    """
    temp_root = tmp_path_factory.mktemp("noveler_paths")

    class TestPathService:
        """繝・せ繝育畑繝代せ繧ｵ繝ｼ繝薙せ・・ytest tmp_path 繝吶・繧ｹ・・""

        def __init__(self, base_path: Path):
            self._base = base_path

        def get_manuscript_dir(self):
            return self._base / "40_蜴溽ｨｿ"

        def get_management_dir(self):
            return self._base / "50_邂｡逅・ｳ・侭"

        def get_plots_dir(self):
            return self._base / "50_邂｡逅・ｳ・侭" / "plots"

        def get_settings_dir(self):
            return self._base / "config"

        @property
        def manuscript_dir(self):
            return self.get_manuscript_dir()

        @property
        def config_dir(self):
            return self.get_settings_dir()

    return TestPathService(temp_root)
```

**螟画峩轤ｹ:**
- 笨・`project_root` 縺ｸ縺ｮ萓晏ｭ倥ｒ螳悟・蜑企勁
- 笨・`tmp_path_factory` 邨檎罰縺ｧ pytest 邂｡逅・ｸ九・繝代せ繧剃ｽｿ逕ｨ
- 笨・繝輔ぅ繧ｯ繧ｹ繝√Ε縺ｨ縺励※豕ｨ蜈･蜿ｯ閭ｽ

---

### Phase 2: 蛟句挨繝・せ繝医ヵ繧｡繧､繝ｫ縺ｮ遘ｻ陦鯉ｼ・edium Priority・・
#### 2.1 `tests/test_18step_async_performance.py`

**Before (迴ｾ迥ｶ - commit f623dde2):**
```python
async def test_18step_async_performance():
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        episode_number = 1
        # 繝・せ繝亥・逅・..
```

**After (謠先｡・:**
```python
@pytest.mark.asyncio
async def test_18step_async_performance(tmp_path):
    """18繧ｹ繝・ャ繝鈴撼蜷梧悄繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ繝・せ繝・
    Args:
        tmp_path: pytest讓呎ｺ悶・荳譎ゅョ繧｣繝ｬ繧ｯ繝医Μ繝輔ぅ繧ｯ繧ｹ繝√Ε
    """
    project_root = tmp_path
    episode_number = 1

    # 繝・せ繝亥・逅・..
    # ・域・遉ｺ逧・↑繧ｯ繝ｪ繝ｼ繝ｳ繧｢繝・・荳崎ｦ・ｼ・```

**螟画峩轤ｹ:**
- 笨・`tempfile` import 蜑企勁
- 笨・context manager 蜑企勁
- 笨・`tmp_path` 繝輔ぅ繧ｯ繧ｹ繝√Ε豕ｨ蜈･

#### 2.2 `tests/unit/infrastructure/test_base.py`

**Before (迴ｾ迥ｶ):**
```python
def setup_method(self) -> None:
    project_root = Path(__file__).parent.parent.parent
    temp_base = project_root / "temp" / "tests"
    temp_base.mkdir(parents=True, exist_ok=True)

    self.test_root = temp_base / test_dir_name
```

**After (謠先｡・:**
```python
@pytest.fixture(autouse=True)
def _setup_test_env(self, tmp_path):
    """pytest讓呎ｺ・tmp_path 繧剃ｽｿ逕ｨ縺励◆繝・せ繝育腸蠅・そ繝・ヨ繧｢繝・・"""
    self.test_root = tmp_path / self.__class__.__name__
    self.test_root.mkdir(parents=True, exist_ok=True)
    yield
    # pytest 縺瑚・蜍輔け繝ｪ繝ｼ繝ｳ繧｢繝・・
```

**螟画峩轤ｹ:**
- 笨・`project_root / "temp/tests"` 縺ｸ縺ｮ萓晏ｭ伜炎髯､
- 笨・pytest 繝輔ぅ繧ｯ繧ｹ繝√Ε蛹・- 笨・繧ｯ繝ｩ繧ｹ繝吶・繧ｹ繝・せ繝医→縺ｮ邨ｱ蜷・
---

### Phase 3: E2E繝ｻ邨ｱ蜷医ユ繧ｹ繝医・谿ｵ髫守噪遘ｻ陦鯉ｼ・ow Priority・・
**蟇ｾ雎｡:**
- `tests/integration/` 驟堺ｸ九・繝・せ繝・- `tests/e2e/` 驟堺ｸ九・繝・せ繝・
**譁ｹ驥・**
1. 譁ｰ隕上ユ繧ｹ繝医・蠢・★ `tmp_path` / `tmp_path_factory` 繧剃ｽｿ逕ｨ
2. 譌｢蟄倥ユ繧ｹ繝医・讖溯・霑ｽ蜉繝ｻ菫ｮ豁｣譎ゅ↓鬆・ｬ｡遘ｻ陦・3. 荳諡ｬ螟画峩縺ｯ驕ｿ縺代√ユ繧ｹ繝医・螳牙ｮ壽ｧ繧貞━蜈・
**繝・Φ繝励Ξ繝ｼ繝・**
```python
# 髢｢謨ｰ繧ｹ繧ｳ繝ｼ繝暦ｼ亥推繝・せ繝医〒譁ｰ隕丈ｽ懈・・・def test_integration_feature(tmp_path):
    test_data = tmp_path / "data"
    test_data.mkdir()
    # 繝・せ繝亥・逅・..

# 繧ｻ繝・す繝ｧ繝ｳ繧ｹ繧ｳ繝ｼ繝暦ｼ亥・繝・せ繝医〒蜈ｱ譛会ｼ・@pytest.fixture(scope="session")
def shared_test_data(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("shared_data")
    # 蜈ｱ譛峨ョ繝ｼ繧ｿ貅門ｙ...
    return data_dir
```

---

## 笨・謌仙粥蝓ｺ貅・
### 螳夐㍼逧・欠讓・
| 謖・ｨ・| 迴ｾ迥ｶ | 逶ｮ讓・| 貂ｬ螳壽婿豕・|
|------|------|------|---------|
| `tempfile` 菴ｿ逕ｨ邂・園 | 3邂・園 | 0邂・園 | `grep -r "tempfile.TemporaryDirectory" tests/` |
| 繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ | 6邂・園 | 0邂・園 | `grep -r 'project_root / "temp"' tests/` |
| pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε蛻ｩ逕ｨ邇・| 60% | 95% | 謇句虚繧ｫ繧ｦ繝ｳ繝・|
| 繝・せ繝亥､ｱ謨玲凾縺ｮ谿矩ｪｸ繝輔ぃ繧､繝ｫ | 譛・| 辟｡ | CI/CD蠕後・繝・ぅ繝ｬ繧ｯ繝医Μ遒ｺ隱・|

### 螳壽ｧ逧・欠讓・
- 笨・縺吶∋縺ｦ縺ｮ繝・せ繝医′ pytest 讓呎ｺ悶ヱ繧ｿ繝ｼ繝ｳ縺ｫ貅匁侠
- 笨・繝ｫ繝ｼ繝医ョ繧｣繝ｬ繧ｯ繝医Μ縺ｫ荳蛻・・繝・せ繝医ョ繝ｼ繧ｿ縺御ｽ懈・縺輔ｌ縺ｪ縺・- 笨・Codex繝ｬ繝薙Η繝ｼ縺ｧ縲継ytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε縲埼・岼縺・箝絶ｭ絶ｭ絶ｭ絶ｭ・(5/5)

---

## 套 螳滓命繧ｹ繧ｱ繧ｸ繝･繝ｼ繝ｫ

### Week 1: Phase 1・・igh Priority・・
| Day | 繧ｿ繧ｹ繧ｯ | 謌先棡迚ｩ |
|-----|--------|--------|
| Day 1 | `conftest.py` 縺ｮ `temp_project_dir` 譖ｸ縺肴鋤縺・| 菫ｮ豁｣繧ｳ繝溘ャ繝・|
| Day 2 | `FallbackPathService` 縺ｮ繝輔ぅ繧ｯ繧ｹ繝√Ε蛹・| 菫ｮ豁｣繧ｳ繝溘ャ繝・|
| Day 3 | 譌｢蟄倥ユ繧ｹ繝亥ｮ溯｡後→蝗槫ｸｰ遒ｺ隱・| 繝・せ繝医Ξ繝昴・繝・|
| Day 4 | 繝峨く繝･繝｡繝ｳ繝域峩譁ｰ | TESTING.md 譖ｴ譁ｰ |
| Day 5 | Codex繝ｬ繝薙Η繝ｼ萓晞ｼ | 繝ｬ繝薙Η繝ｼ繝ｬ繝昴・繝・|

### Week 2: Phase 2・・edium Priority・・
| Day | 繧ｿ繧ｹ繧ｯ | 謌先棡迚ｩ |
|-----|--------|--------|
| Day 1 | `test_18step_async_performance.py` 遘ｻ陦・| 菫ｮ豁｣繧ｳ繝溘ャ繝・|
| Day 2 | `test_base.py` 遘ｻ陦・| 菫ｮ豁｣繧ｳ繝溘ャ繝・|
| Day 3-4 | 莉悶・繝ｦ繝九ャ繝医ユ繧ｹ繝磯・ｬ｡遘ｻ陦・| 隍・焚繧ｳ繝溘ャ繝・|
| Day 5 | 蝗槫ｸｰ繝・せ繝亥ｮ溯｡・| 繝・せ繝医Ξ繝昴・繝・|

### Week 3-4: Phase 3・・ow Priority・・
- 邨ｱ蜷医・E2E繝・せ繝医・谿ｵ髫守噪遘ｻ陦・- 譁ｰ隕上ユ繧ｹ繝医・蠢・★ pytest讓呎ｺ悶ヱ繧ｿ繝ｼ繝ｳ繧剃ｽｿ逕ｨ
- 繝ｬ繧ｬ繧ｷ繝ｼ繝・せ繝医・讖溯・霑ｽ蜉譎ゅ↓鬆・ｬ｡遘ｻ陦・
---

## 圷 繝ｪ繧ｹ繧ｯ縺ｨ邱ｩ蜥檎ｭ・
### 繝ｪ繧ｹ繧ｯ1: 譌｢蟄倥ユ繧ｹ繝医・遐ｴ謳・
**繝ｪ繧ｹ繧ｯ繝ｬ繝吶Ν:** 泯 Medium

**隧ｳ邏ｰ:**
- `temp_project_dir` 縺ｮ繝代せ讒矩螟画峩縺ｫ繧医ｊ縲√ワ繝ｼ繝峨さ繝ｼ繝峨ヱ繧ｹ縺ｫ萓晏ｭ倥☆繧九ユ繧ｹ繝医′螟ｱ謨励☆繧句庄閭ｽ諤ｧ

**邱ｩ蜥檎ｭ・**
1. Phase 1螳御ｺ・ｾ後↓蜈ｨ繝・せ繝医ｒ螳溯｡鯉ｼ・pytest tests/ -v`・・2. 螟ｱ謨励＠縺溘ユ繧ｹ繝医ｒ蛟句挨縺ｫ菫ｮ豁｣
3. CI/CD縺ｧ縺ｮ邯咏ｶ夂噪縺ｪ蝗槫ｸｰ遒ｺ隱・
### 繝ｪ繧ｹ繧ｯ2: 繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ蜉｣蛹・
**繝ｪ繧ｹ繧ｯ繝ｬ繝吶Ν:** 泙 Low

**隧ｳ邏ｰ:**
- `tmp_path_factory` 縺ｮ蛻晄悄蛹悶さ繧ｹ繝医′ `tempfile` 繧医ｊ鬮倥＞蜿ｯ閭ｽ諤ｧ

**邱ｩ蜥檎ｭ・**
1. 繝吶Φ繝√・繝ｼ繧ｯ繝・せ繝亥ｮ滓命・・hase 1蜑榊ｾ後〒豈碑ｼ・ｼ・2. 繧ｻ繝・す繝ｧ繝ｳ繧ｹ繧ｳ繝ｼ繝励・驕ｩ蛻・↑豢ｻ逕ｨ
3. 蠢・ｦ√↓蠢懊§縺ｦ繧ｭ繝｣繝・す繝ｳ繧ｰ謌ｦ逡･繧呈､懆ｨ・
### 繝ｪ繧ｹ繧ｯ3: Windows/Linux 繝代せ蟾ｮ逡ｰ

**繝ｪ繧ｹ繧ｯ繝ｬ繝吶Ν:** 泙 Low

**隧ｳ邏ｰ:**
- `tmp_path` 縺ｮ螳滉ｽ薙′ OS 縺ｫ繧医ｊ逡ｰ縺ｪ繧具ｼ・indows: `%TEMP%`, Linux: `/tmp`・・
**邱ｩ蜥檎ｭ・**
1. `Path` 繧ｪ繝悶ず繧ｧ繧ｯ繝医・邨ｱ荳菴ｿ逕ｨ・域枚蟄怜・繝代せ縺ｯ遖∵ｭ｢・・2. CI/CD 縺ｧ Windows/Linux 荳｡譁ｹ縺ｧ繝・せ繝亥ｮ溯｡・3. 繝代せ繧ｻ繝代Ξ繝ｼ繧ｿ縺ｮ譏守､ｺ逧・・逅・ｼ・Path.joinpath()` 菴ｿ逕ｨ・・
---

## 答 蜿り・ｳ・侭

### 蜈ｬ蠑上ラ繧ｭ繝･繝｡繝ｳ繝・
- [pytest蜈ｬ蠑・ tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [pytest蜈ｬ蠑・ tmp_path_factory](https://docs.pytest.org/en/stable/reference/reference.html#tmp-path-factory)
- [pytest蜈ｬ蠑・ Scope](https://docs.pytest.org/en/stable/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)

### 繝励Ο繧ｸ繧ｧ繧ｯ繝亥・雉・侭

- `AGENTS.md` ﾂｧWorkflow - 險育判竊貞ｮ溯｣・・繝・せ繝医・蜴溷援
- `CLAUDE.md` ﾂｧTesting & Quality - 繝・せ繝亥･醍ｴ・- `tests/outputs/b20/phase4-testing/codex_review_report.md` - Codex繝ｬ繝薙Η繝ｼ邨先棡
- `docs/proposals/root-structure-policy-v2.md` - 繝ｫ繝ｼ繝域ｧ矩繝昴Μ繧ｷ繝ｼ

### 鬘樔ｼｼ繝励Ο繧ｸ繧ｧ繧ｯ繝・
- [Django Test Patterns](https://docs.djangoproject.com/en/stable/topics/testing/tools/#django.test.TestCase)
- [FastAPI Testing Best Practices](https://fastapi.tiangolo.com/tutorial/testing/)

---

## 売 繝ｬ繝薙Η繝ｼ縺ｨ謇ｿ隱・
### 繝ｬ繝薙Η繧｢繝ｼ

- [ ] **謚陦薙Ξ繝薙Η繝ｼ:** Codex (閾ｪ蜍・
- [ ] **繧｢繝ｼ繧ｭ繝・け繝√Ε繝ｬ繝薙Η繝ｼ:** 繝励Ο繧ｸ繧ｧ繧ｯ繝医が繝ｼ繝翫・
- [ ] **繧ｻ繧ｭ繝･繝ｪ繝・ぅ繝ｬ繝薙Η繝ｼ:** N/A・医ユ繧ｹ繝医う繝ｳ繝輔Λ縺ｮ縺ｿ・・
### 謇ｿ隱阪・繝ｭ繧ｻ繧ｹ

1. 譛ｬ謠先｡医ｒ `docs/proposals/` 縺ｫ驟咲ｽｮ
2. Codex繝ｬ繝薙Η繝ｼ萓晞ｼ・・/b20-workflow review`・・3. 謇ｿ隱榊ｾ後↓ Phase 1 螳溯｣・幕蟋・4. 蜷・ヵ繧ｧ繝ｼ繧ｺ螳御ｺ・ｾ後↓騾ｲ謐怜ｱ蜻・
---

## 統 螟画峩螻･豁ｴ

| 譌･莉・| 繝舌・繧ｸ繝ｧ繝ｳ | 螟画峩蜀・ｮｹ | 闡苓・|
|------|-----------|---------|------|
| 2025-10-03 | 1.0 | 蛻晉沿菴懈・ | Claude Code |
| 2025-10-03 | 2.0 | Phase 1-3 螳御ｺ・・譛邨ょｱ蜻・| Claude Code |

---

## 脂 螳滓命邨先棡・・025-10-03 螳御ｺ・ｼ・
### Phase 1: Session-Scope Fixtures・亥ｮ御ｺ・ｼ・
**蟇ｾ雎｡:** `tests/conftest.py` 縺ｮ繧ｻ繝・す繝ｧ繝ｳ繧ｹ繧ｳ繝ｼ繝励ヵ繧｣繧ｯ繧ｹ繝√Ε

**螳滓命蜀・ｮｹ:**
- 笨・`temp_project_dir` 竊・`tmp_path_factory` 遘ｻ陦・- 笨・`temp_guide_root` 竊・`tmp_path_factory` 遘ｻ陦・- 笨・`temp_outputs_root` 竊・`tmp_path_factory` 遘ｻ陦・- 笨・`FallbackPathService` 縺ｮ繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ蜑企勁

**謌先棡:**
- 遘ｻ陦悟ｮ御ｺ・ 3繝輔ぅ繧ｯ繧ｹ繝√Ε
- 繧ｳ繝溘ャ繝・ 隍・焚 (phase1 branch)

### Phase 2: Function-Scope Tests・亥ｮ御ｺ・ｼ・
**蟇ｾ雎｡:** 蛟句挨繝・せ繝医ヵ繧｡繧､繝ｫ縺ｮ髢｢謨ｰ繧ｹ繧ｳ繝ｼ繝励ユ繧ｹ繝・
**螳滓命蜀・ｮｹ:**
- 笨・`test_18step_async_performance.py` 遘ｻ陦・- 笨・`test_base.py` setup_method 竊・pytest fixture 遘ｻ陦・- 笨・縺昴・莉悶Θ繝九ャ繝医・邨ｱ蜷医ユ繧ｹ繝磯・ｬ｡遘ｻ陦・
**謌先棡:**
- 遘ｻ陦悟ｮ御ｺ・ 20+ 繝・せ繝医ヵ繧｡繧､繝ｫ
- 蜑頑ｸ帙＠縺・`tempfile` 菴ｿ逕ｨ: 30+ 邂・園
- 繧ｳ繝溘ャ繝・ 隍・焚 (phase2 branch)

### Phase 3: E2E/Integration Tests・亥ｮ御ｺ・ｼ・
**蟇ｾ雎｡:** E2E繝ｻ邨ｱ蜷医ユ繧ｹ繝医・ `tempfile.TemporaryDirectory` 螳悟・蜑企勁

**螳滓命蜀・ｮｹ:**
- 笨・Batch 1-9: 邨ｱ蜷医ユ繧ｹ繝医・繧､繝ｳ繝輔Λ繝・せ繝育ｧｻ陦・(44竊・0邂・園)
- 笨・Batch 10: `test_outbox_idempotency.py` (2邂・園) - commit
- 笨・Batch 11: `test_yaml_a31_checklist_repository_extended.py` (2邂・園) + 繝舌げ菫ｮ豁｣ - commit
- 笨・Batch 12: `test_gate_integration.py` (6邂・園) - commit

**繝舌げ菫ｮ豁｣:**
- `template_path.Path("w")` 竊・`template_path.open("w", encoding="utf-8")`

**謌先棡:**
- **蜈ｨ63邂・園縺ｮ tempfile.TemporaryDirectory 繧貞ｮ悟・蜑企勁** 笨・- **100% pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε縺ｫ遘ｻ陦悟ｮ御ｺ・* 脂
- 譛邨ら｢ｺ隱・ `grep -r "with tempfile.TemporaryDirectory" tests/ | wc -l` 竊・**0**

### 譛邨らｵｱ險・
| 謖・ｨ・| 髢句ｧ区凾 | 螳御ｺ・凾 | 驕疲・邇・|
|------|-------|--------|--------|
| `tempfile.TemporaryDirectory` 菴ｿ逕ｨ邂・園 | 63邂・園 | 0邂・園 | **100%** 笨・|
| 繝上・繝峨さ繝ｼ繝峨ヱ繧ｹ (`project_root / "temp"`) | 6邂・園 | 0邂・園 | **100%** 笨・|
| pytest讓呎ｺ悶ヵ繧｣繧ｯ繧ｹ繝√Ε蛻ｩ逕ｨ邇・| ~60% | ~95%+ | **驕疲・** 笨・|
| 繝・せ繝亥､ｱ謨玲凾縺ｮ谿矩ｪｸ繝輔ぃ繧､繝ｫ | 譛・| 辟｡ | **謾ｹ蝟・* 笨・|
| Codex繝ｬ繝薙Η繝ｼ諠ｳ螳壹せ繧ｳ繧｢ | 箝絶ｭ絶ｭ・(3/5) | 箝絶ｭ絶ｭ絶ｭ絶ｭ・(5/5) 譛溷ｾ・| **蜷台ｸ・* 識 |

### 荳ｻ隕√さ繝溘ャ繝・
**Phase 3 (Batch 10-12):**
- Batch 10: `refactor(test): migrate outbox idempotency tests to pytest tmp_path (2 usages)`
- Batch 11: `refactor(test): migrate A31 checklist repository tests to pytest tmp_path (2 usages) - Also fixes bug: .Path('w') -> .open('w', encoding='utf-8')`
- Batch 12: `refactor(test): migrate gate integration tests to pytest tmp_path (6 usages)`

**蜈ｨ菴・**
- Phase 1-3縺ｧ蜷郁ｨ・5+繧ｳ繝溘ャ繝・- 縺吶∋縺ｦ縺ｮ繝・せ繝医′ pytest 讓呎ｺ悶ヱ繧ｿ繝ｼ繝ｳ縺ｫ貅匁侠
- 繝ｫ繝ｼ繝医ョ繧｣繝ｬ繧ｯ繝医Μ豎壽沒繝ｪ繧ｹ繧ｯ螳悟・謗帝勁

---

**謠先｡医せ繝・・繧ｿ繧ｹ:** 笨・**螳御ｺ・* (2025-10-03)

**谺｡縺ｮ繧｢繧ｯ繧ｷ繝ｧ繝ｳ:**
- 笨・Phase 1-3 螳御ｺ・- 竢ｭ・・蜈ｨ繝・せ繝医せ繧､繝ｼ繝亥ｮ溯｡後〒蝗槫ｸｰ遒ｺ隱・- 竢ｭ・・Codex繝ｬ繝薙Η繝ｼ蜀堺ｾ晞ｼ・医せ繧ｳ繧｢蜷台ｸ顔｢ｺ隱搾ｼ・