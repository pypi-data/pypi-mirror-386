![Pyversion](https://img.shields.io/badge/dynamic/json?query=info.requires_python&label=python&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fgeojson-rewind%2Fjson)
![PyPI](https://img.shields.io/pypi/v/dspawpy?label=pypi%20package)
![PyPI - Downloads](https://static.pepy.tech/badge/dspawpy/month)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

# Introduction （简介）

dspawpy is a post-processing tool mainly for DFT package [DS-PAW](https://cloud.hzwtech.com/web/product-service?id=10), providing some functions of data capture, conversion, structure conversion, and drawing. （dspawpy 主要是 [DS-PAW](https://cloud.hzwtech.com/web/product-service?id=10) 软件的后处理辅助工具，提供一些数据抓取、换算、结构转化、绘图功能）

## Online tutorial（在线教程）

Visit（移步） <http://hzwtech.com/Device%20Studio/DS-PAW/build/html/tools.html>

You can also download PDF and EPUB there for off-line reading. （也可以在那下载到PDF和EPUB格式的文档供离线使用）

## Installation （安装）

Either by pip: （通过pip安装）

```bash
pip install dspawpy
```

Or by conda: （通过conda安装）

```bash
conda install -c conda-forge dspawpy
```

## CHANGELOG （版本更新简述）

### 1.8.4

- BUG修复：修复构建配置

### 1.8.3

- BUG修复：项目描述修正

### 1.8.2

- 新功能：支持结构输出为 png/gif 格式（添加 ase 依赖）
- BUG修复：能带反折叠功能的 x 轴范围取消硬编码限制，改为根据实际 kpoints 数量自动调整
- BUG修复：8.1 NEB 插值功能的周期性边界条件参数处理
- 细节优化：简化文档构建脚本
- 文档优化：支持中英文多版本文档构建

### 1.8.1

- BUG修复: 14 结构优化信息提取模块导入
- BUG修复: README 信息修正

### 1.8.0

- 新功能： 允许提取 band/dos 数据 csv
- 细节优化: 8.7 monitor_force_energy 功能，允许不同构型的离子步不同，此时会以最大共有离子步为基准线，不足的构型的相应数据将用空值填充。另外，智能处理续算情况，将自动忽略以前的计算任务中的离子步。
- BUG修复: 14 结构优化信息提取时提示词含义不明，并提升代码效率

### 1.7.4

- 新功能： neb 的 monitor_force_energy() 函数增加 relative 选项，显示相对于最后一步的值
- BUG修复： NEB 插值时如果端点结构是 Fix 和 Mag 的写法，Mag未能正确解析。现在插值结构的初始磁矩保持和初始结构的一致
- BUG修复： python 版本要求从 3.8 改成 3.9

### 1.7.3

- 新功能： 命令行交互工具dspawpy的8.1插值NEB构型增加一个周期性边界条件开关，打开后将根据晶胞周期性平移原子
- BUG修复: 初末态是笛卡尔坐标写法时8.4功能xyz格式的neb链的中间构型未修改成笛卡尔坐标
- BUG修复: 修复json格式的neb链在DeviceStudio中打开时若误触convergence选项卡将卡死的问题
- 细节优化: 8.3以及其他调用到polars表格的地方如果表格行列数过多自动折叠，这一选项现在可以通过设置环境变量 ALWAYS_EXPAND = True 来修改，注意，对于 8.7 monitor_force_energy 功能，最多只会展示开始和结束前五个离子步信息，如果要更多数据，请参考用户脚本将csv数据另行导出

### 1.7.2

- 新功能： plot_dos 函数增加了 ax 参数，便于自行组合子图
- BUG修复: 纠正了体积数据可视化任务elf与其他4类体积数据的解析在部分场景中错乱的问题
- BUG修复: DOS单位移除多余的 Angstrom^3

### 1.7.1

- BUG修复: 修正命令行工具新增功能中一个单双引号混用导致的3.12以下版本python不兼容的问题
- 细节优化: 从hdf5文件中读取数据时，将np.array函数替换成np.asarray，避免出现不可复制的警告信息

### 1.7.0

- 新功能：DS-PAW 结构优化过程监控，编号14，用于查看"能量"、"最大原子受力"、"构型"三者随着离子步数的变化，同时生成优化过程轨迹xyz文件和最小受力对应构型
- 新功能：h5 文件内容查看，编号15，可以预览h5文件数据组织结构、并查询任意具体数值
- BUG修复： neb_chain_json/xyz 函数未能正确从latestStructureXX.as中解析坐标信息，可能导致中间构型的优化后的结构无法用DeviceStudio查看，现已修正
- 细节优化：提示词修正
- 细节优化：用户脚本，bandDos二者费米能级不一致时，默认以DOS数据为准将二者对齐

### 1.6.0

- 重要变更： 电荷密度分析模块，write_VESTA, write_delta_rho_vesta 两个函数不再要求指定数据格式format参数，而是优先尝试从输出文件名后缀中判断，比如输出到 a.cube 那么数据就以cube格式写入，如果输出到 a.vesta 那么数据就以vesta格式写入。如果没有后缀，比如输出到a，那么默认以cube格式写入。cli31和32部分移除数据格式询问语句
- 重要变更：文件名冲突时的默认行为从“将原文件改名成带时间后缀形式”变更为“将新文件改名为带时间后缀形式”
- 新功能： 增加环境变量 OVERWRITE 用于控制文件名冲突时程序的行为（用于neb备份和保存结构文件，此参数对保存图片无效，请手动备份）。yes表示直接覆盖文件（夹），no表示放弃写入，bk表示备份原文件（夹）为带时间后缀的形式，default表示将新文件的名称改成带时间后缀的形式。用法示例： `OVERWRITE=yes dspawpy`
- 新功能： 差分电荷密度从 rho 扩展到支持 elf, pcharge, potential 物理量
- BUG修复： volumetricData 三维可视化时 elf, pcharge, potential 数组顺序解析不当
- BUG修复： neb备份的时候，如果存在一些不常见的文件或文件夹，程序可能会中断，此版本修复了这个异常

### 1.5.5

- BUG修复： cli改名dspawpy，否则无法在windows上安装使用

### 1.5.4

- BUG修复： cli部分功能提示词错误
- BUG修复： 手册版本号未正确更新

### 1.5.3

- BUG修复： nebtools最大受力栏顺序有误
- 功能强化： nebtools收敛过程监控函数，允许首尾两个不参与NEB计算的文件夹存在，保存图片前自动创建文件夹

### 1.5.2

- BUG修复： nebtools由于一处混用f表达式和%表达式造成python<3.12不兼容
- BUG修复： cli2增加支持hzw和xyz输入文件的提示

### 1.5.1

- 重要变更： 移除better_exceptions依赖，用户应自行安装并设置然后使用，而不是在dspawpy中强制启用。

### 1.5.0

- 新功能： 支持读取hzw分子结构
- 新功能： 支持读取xyz分子结构
- 重要变更： 移除内置的 logger.catch 修饰器，使错误输出更精简
- 重要变更： 添加better_exceptions库，用于诊断python标准报错信息中的变量值
- BUG修复： cli部分绘图功能保存空白图片
- BUG修复： cli 3_3 同时选择多个轴
- BUG修复： neb 续算功能的日志输出未正常显示备份文件夹路径
- 其他： DLL=debug python *.py 可以显示DEBUG级别的日志信息

### 1.4.1

- BUG修复： 包路径设置错误导致cli无法正常启动
- BUG修复： nebtools.printef 也设置隐藏表格头的数据类型

### 1.4.0

- 新功能： NEB计算过程中，可以一键绘制受力和能量的变化趋势图；详见手册8.7节
- 重要变更： neb打印表格信息时不再显示数据类型，让表格更精简
- BUG修复： neb 初始结构插值，补充 pbc 参数，用于指定是否利用周期性边界条件选择最短扩散路径
- BUG修复： write 模块将 structures 参数类型从 list 扩展到 Sequence 以兼容元组、numpy数组等任意可寻址序列
- BUG修复： banddos 用户脚本和cli默认的投影方式不正确，导致出现用户警告

### 1.3.4

- 重要变更： cli 主菜单增加q退出选项，完成一个任务后会询问是否继续，减少重复启动cli的耗时
- BUG修复： 光学性质绘图未正确将不同性质绘制在同一张图中（被清空且图例不合理）
- BUG修复： cli 进入子菜单后无法使用0返回

### 1.3.3

- BUG修复： 修正cli功能2的提示词中的细节错误，写明具体的文件名匹配规则
- BUG修复： 修正cli功能12和13的提示词中的细节

### 1.3.2

- 重要变更： 使用python3.8以下版本将无法启动程序
- 重要变更： 正式用 polars 库替换 pandas 库
- BUG修复： 移除setup.py中已不存在的ecli入口
- BUG修复： wannier.json 不存在 SpinType 键导致读取失败
- BUG修复： 瓦尼尔能带对比时，未正确读取 system.json 中的费米能级信息

### 1.3.1

- BUG修复： 修复userscripts和cli中的一些问题
- BUG修复： 修复json文件读取函数中的导包语句缺失问题
- 功能强化： 10.2 支持读取aimd.json文件绘制物理量变化曲线图（仅无法读取压力变化）

### 1.3.0

- 重要变更： 不再支持python3.8（不含）以下版本
- 重要变更： 合并cli.py和cli_en.py，通过命令行选项 -l 或 --language 切换交互提示语言
- 重构： 命令行交互程序增加静默运行模式，便于编程调用
- 重构： 命令行交互程序大幅提高可读性，在等待用户输入同时多线程动态载入最终调用的函数
- 重构： 懒导入——将导包语句从文件开头尽量移入函数中，避免导入不必要模块，减少导包耗时
- 重构： 绝大多数参数补充类型提示，解决所有已知的静态检查问题
- 体验优化： cli在输入部分参数时增加Tab键获取提示的功能
- 体验优化： cli增加命令行参数帮助菜单
- 体验优化： 全局使用 loguru 库的 catch 修饰器，控制报错信息的详细程度
- 体验优化:  average_along_axis potential类型支持自动判断内部subtype类型为 TotalLocalPotential 的情况
- 体验优化： 用 polars 库替换了 pandas 库，加速处理多维数据
- BUG修复： write_vesta 插值体积数据部分变量未及时更新
- BUG修复： rdf 修复 density 变量缺失的问题
- BUG修复： cli 8.4 neb

### 1.2.2

- BUG修复： dos和band读取非线性自旋算例的 h5/json 输出文件时，对自旋判断不准

### 1.2.0

- 体验优化： cli将导包语句从文件开头移入函数中，大幅减少python脚本的import时间
- 体验优化： cli增加模糊匹配功能
- 体验优化： optical绘图默认绘制全部数据以便查看
- 体验优化： neb备份时如果目标文件夹已存在，将原先的改名成附加时间戳的文件夹
- BUG修复： dos非线性自旋时无法读取h5/json数据

### 1.1.9

- BUG修复： 修复cli的一些已知bug

### 1.1.8

- 功能强化： 体数据（volumetric data）支持自定义网格插值（调用scipy的RegularGridInterpolator插值器）；增加 txt 格式支持，每行包含格点的 xyz 坐标和具体数值

### 1.1.7

- BUG修复： 修复conda install dspawpy后cli没有同步安装导致无法唤起的故障
- BUG修复： 移除 plot_dos 函数中 xlim、ylim两个参数类型提示，以避免python<3.9的运行错误
- BUG修复： 老版本python, pymatgen, monty等第三方库的兼容性问题

### 1.1.6

- 重要变更： cli 环境部署模块改成dspawpy更新模块，因为现在cli内置于dspawpy中，在hzw机器上唤起cli必定已经source环境了，不再需要原先的1.1功能；仅保留原先的1.2功能，即升级dspawpy
- BUG修复： 移除 plot_dos 函数中 xlim、ylim两个参数类型提示时使用的 | 符号（需要python3.10支持），以避免python<3.10的运行错误

### 1.1.5

- 功能强化： 从pmg中提取plot_dos函数，增加raw参数用于输出投影态密度绘图坐标点数据到dos_raw.csv，使用案例请参考辅助工具使用教程——dos部分

### 1.1.4

- BUG修复： cli 5-6 d带中心参数传递错误
- BUG修复： cli 7-1 内部传参错误
- BUG修复： structure结构写成文件时应采用元素符号而不是带电荷的species
- BUG修复： __init__.py 中版本号未及时更新(影响1.1.2和1.1.3两个版本)

### 1.1.3

- BUG修复： 增加cli所需两个依赖，移除python3.12的语法警告

### 1.1.2

- 功能强化： cli 默认调用 agg 作为matplotlib的绘图后端，避免在某些linux服务器上由于X11转发未设置导致的QT相关问题
- 功能强化： cli 优化NEB链功能提示语
- BUG修复： 兼容python3.12和numpy>1.24
- BUG修复： 用户脚本兼容新旧pymatgen
- BUG修复： NEB续算默认备份文件夹改名成backup

### 1.1.1

- 重要变更： cli并入dspapwy，不需要再去官网下载cli了
- 功能强化： cli多处细节优化，提升交互体验
- 功能强化： 增加 dump_bs_raw() 和 dump_dos_raw() 函数，功能有限

### 1.1.0

- BUG修复： io.write.write_VESTA() 和 io.write.write_delta_rho_vesta() 增加 inorm 参数，用于控制是否归一化（默认关闭）
- 功能强化： io.write.write_VESTA() 和 io.write.write_delta_rho_vesta() 增加 compact 参数，可以在不影响VESTA显示效果的前提下，减小写出的文件（如 .cube ）体积（默认关闭）
- 功能强化： 新增 bdplot() 函数（基于pymatgen的BSDOSPlotter类的get_plot函数优化），用于绘制能带态密度图，详见手册说明

### 1.0.9

- BUG修复： as结构文件中的原子自由度标签可以将 Fix_x Fix_y Fix_z 缩写为 Fix，其他内容不变
- 重要变更： 使用 diffusion.nebtools.write_json_chain/write_xyz_chain() 生成NEB链时如果step=-1，则优先读取 latestStructureXX.as，失败后尝试 nebXX.h5，最后尝试 nebXX.json；可以使用 ignorels 参数忽略 latestStructureXX.as

### 1.0.8

- BUG修复： 准备弃用的 build_Structures_from_datafile() 未返回结构，read() 不受影响；其他调用 build_Structures_from_datafile() 的函数改为调用 read
- BUG修复： 修复 io.read.get_band_data() 考虑自旋且设置了zero_to_efermi时，自旋向下能带数据解析错误的问题
- 功能强化： io.structure模块新增 read() 代替 build_Structures_from_datafile()，write() 代替 io.write.to_file()，convert() 封装 read() 和 write() 函数，便于快速调用

### 1.0.5

- 功能强化： to_file() 写pdb文件时，结构可以不含晶胞信息

### 1.0.4

- BUG修复： build_Structures_from_datafile()选择原子序号时上限设置，h5文件里最后一个离子步信息改成尝试读取
- 功能强化： build_Structures_from_datafile()支持读取pdb格式
- 细节修改： AIMD读不到PressureKinetic信息时增加相应警告

### 1.0.3

- BUG修复： 解决浮点数过大时volumetricData相关文件浮点数粘在一起的问题
- BUG修复： plot_barrier()读取neb.h5/json绘制能垒图时，反应坐标依旧累加
- BUG修复： plot_bandunfolding()能带反折叠费米能级被默认置零
- 功能强化： 新增cube格式用于保存volumetricData
- 功能强化： 全局支持相对路径与绝对路径混写
- 功能强化： datafile参数以及io.read以及diffusion.nebtools模块中的相应参数，可以是文件位置，也可以是文件所在的文件夹路径
- 功能强化： build_Structures_from_datafile()增加task参数，用于配合datafile为文件夹路径的情况
- 重要变更： 移除中文提示语句，精简提示信息
- 重要变更： volumetricData默认使用cube格式写入
- 重要变更： 移除thermo_correction()，一个单纯的外包装函数
- 细节修改： 保存图片或文件时，统一使用 ==> 标记文件绝对路径

### 1.0.2

- BUG修复：  当存在Fix或Mag信息时，structure.as 坐标类型可能解析错误的问题
- 功能强化： 预览NEB链条函数改名 write_xyz(json)_chain，增加dst参数制定保存路径
- 功能强化： potential 中数据集不预作限制
- 功能强化： get_lagtime_msd, get_lagtime_rmsd 自动从数据文件中读取timestep（以前必须手动指定）
- 细节修改： 优化部分提示语句

### 1.0.1

- BUG修复： to_file绑定filename参数，避免老版本pymatgen的兼容性问题
- BUG修复： average_along_axis的task参数改成大小写敏感，避免rhoBound任务类型解析错误
- 功能强化： 将文件存入不存在的目录前，先创建（支持相对路径）
- 功能强化： write_VESTA和average_along_axis增加subtype参数，指定TotalLocalPotential数据

### 1.0.0

- BUG修复： 文件开头增加utf8编码声明
- 功能强化： 电荷密度差分支持更多组分（不限二元）
- 重要变更： io.utils的getZPE、getTSads、getTSgas函数，增加参数用于将计算结果存入文件
- 重要变更： io.write.write_VESTA() data_type参数可选值从boundcharge改成rhoBound，且大小写敏感，从而保持与DS-PAW输出文件名相同

### 0.9.9

- BUG修复： 修复新版numpy不支持混用array和list生成数组的问题
- BUG修复： 修复从json文件读能带时zero_to_efermi不生效的问题
- 新增功能： build_Structures_from_datafile模块支持读取 neb.h5 和 phonon.h5 文件
- 重要变更： 移除io模块中冗余的 _json.py （相关功能已整合进其他模块中并有所加强）
- 重要变更： 删除 setup.py 中不需要的 joblib 依赖库

### 0.9.8

- BUG修复： to_file 和 build_Structures_from_datafile 接口统一
- BUG修复： io.write模块涉及的保存文件操作，当目标路径上层文件夹不存在时将自动创建
- BUG修复： io.read.get_band_data的zero_to_efermi参数设置为True时，数据的处理逻辑
- BUG修复： io.read.get_sinfo读取relax.json不再因FixLattice而报错
- 新增选项： nebtools的summary函数，新增show_converge用于控制是否显示收敛图，outdir用于指定收敛图的路径
- 新增功能： 写文件涉及的操作，支持传入路径，而不单是文件名
- 新增功能： nebtools的restart函数支持在Windows机器上操作，不必在旧NEB路径执行，备份路径可随意指定
- 新增功能： nebtools的get_neb_subfolder函数新增return_abs参数，用于返回子文件夹的绝对路径
- 重要变更： nebtools的restart函数删除inputin参数，采用压缩较快的zip方法，将生成zip压缩包而不是tar.xz
- 重要变更： io.read.get_band_data的zero_to_fermi参数改名zero_to_efermi

### 0.9.7

- BUG修复： get_rdf 元素对自己计算RDF时的索引
- 新增选项：to_file 增加 si 参数，支持读入单个structure以及Structure列表

### 0.9.6

- BUG修复： pymatgen支持的几类结构文件的读取接口

### 0.9.5

- 重要变更： get_band_data 的 shift_efermi 参数改名为 zero_to_fermi

### 0.9.4

- 新增功能： get_band_data 增加 shift_efermi 参数
- BUG修复： 电荷密度差分函数移除 numpy 多维数组的 shape 参数
- BUG修复： Fe_1 -> Fe+, Fe_2 -> Fe2+ 用于能带、态密度绘图

### 0.9.3

- 新增功能： 接入pymatgen支持的几类结构文件的读写操作
- 新增功能： 支持通过 `dspawpy.__version__` 查看版本号
- 重要变更： write_xyz_traj, write_dump_traj 并入 to_file 函数
- 细节优化： 大幅提高RDF计算效率

### 0.9.2

- 新增功能： 支持从as文件中解析磁矩和FIX信息
- 新增功能： 从h5/json文件中读取数据时支持指定读取的离子步（从1开始）

### 0.9.1

- 重要变更： 精简合并多个函数，统一调用方法
- 新增功能： 支持合并多个xyz和dump文件
- 细节优化： 读取h5或json文件后若无错误，不再打印空行
- 细节优化： 耗时的RDF计算显示进度百分比

### 0.9.0

- 重要变更： 一些函数合并、所在模块迁移，请确认版本
- 新增功能： 支持读取含多离子步计算结果的h5/json文件中的磁矩信息
- BUG修复： get_band_data 函数指定efermi不生效

### 0.8.9

- BUG修复： d_band 脚本运行错误

### 0.8.8

- 新增功能： 支持读取正在进行中的NEB信息，生成movie轨迹文件（可用DS打开观察）
- 新增功能： 支持NEB转XYZ轨迹文件（可用OVITO打开观察）
- 新增功能： plot_aimd 支持读取多个h5文件画在同一张图中
- BUG修复： 电荷差分处理json文件报错
- BUG修复： 极化曲线标记的数值错误
- BUG修复： neb_movie_*.json 中反应坐标重复累加错误

### 0.8.7

- 代码重构，大幅修改数据结构，加速处理过程
- 支持读取h5格式的输出文件
- 新增AIMD, NEB等部分常用功能

### 0.3.0

- 对应2021A版本DS-PAW，辅助处理一些常见数据文件
