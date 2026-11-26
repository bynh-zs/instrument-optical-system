# 器件型号 / 参数 / 文献 — 联网核实台账

> 核实日期：2026-11-25　核实方式：逐项联网检索厂商官方页、期刊 DOI 页与一手论文，只登记**检索到确实存在**的型号、参数与出处。
> 原则：不臆造型号、卷期、页码、参数与链接；查不到、或来源互相冲突的数值不写入设计，另在文末「未采纳信息」中列出原因。
> 说明：下列 URL 为核实时实际访问的页面；型号与参数以厂商官方页 / 期刊页为准，第三方聚合页仅作交叉印证。

---

## 一、器件型号核实（第 2 项选型依据）

| # | 器件 | 核实型号 | 核实到的关键参数 | 来源（官方页 / 一手文献） |
|---|---|---|---|---|
| 1 | He-Ne 激光器 | **Thorlabs HNL050L** | 632.8 nm；5.0 mW；**线偏振，偏振比 500:1**；TEM₀₀ 纯度 >95%；1/e² 光斑 Ø0.81 mm；发散角 1.0 mrad；纵模间隔 435 MHz；RMS 噪声 0.2%（30 Hz–10 MHz）；8 h 功率漂移 ±2.5%；激光头长 400.56 mm、重 0.59 kg；Class IIIb/3B | Thorlabs 目录 V21 p.1279：https://www.thorlabs.us/catalogpages/V21/1279.pdf ；GoPhotonics 产品页 https://www.gophotonics.com/products/lasers/thorlabs-inc/29-46-hnl050l |
| 2 | 半波片 HWP | **Thorlabs WPH05M-633** | Ø1/2″ 零级（复合）半波片，Ø1″ 安装座；中心波长 633 nm；λ/2 延迟，精度 <λ/300；晶体石英，空气间隔；通光孔径 Ø10 mm；透射波前误差 λ/8 @633 nm；单面反射率 <0.25%；表面质量 20-10；光束偏离 0°±10″ | 官方页 https://www.thorlabs.de/thorproduct.cfm?partnumber=WPH05M-633 ；参数交叉印证 https://www.meetoptics.com/polarization-optics/waveplates/half-waveplate/s/thorlabs/p/WPH05M-633 |
| 3 | 起偏器 GL | **Thorlabs GL10-A**（Glan-Laser 方解石偏振器） | 通光孔径 Ø10 mm；AR 镀膜 350–700 nm；**消光比 100 000:1**；激光级天然方解石、低散射；透射波前畸变 λ/4 @633 nm；表面质量 20-10；光束偏离 3 arcmin；尺寸 12.2×13.7 mm；CW 损伤阈值 500 W/cm² | 官方页 https://www.thorlabs.com/glan-laser-calcite-polarizers 、中文页 https://www.thorlabs.com/zh/glan-laser-calcite-polarizers ；参数页 https://www.gophotonics.com/products/polarizers/thorlabs-inc/36-46-gl10-a ；BAM 实际用例（俄亥俄州立学位论文）https://research.cbc.osu.edu/allen.697/wp-content/uploads/2011/09/thesis_castada-8-5-10-v3.pdf |
| 4 | 无限远校正长工作距物镜 Obj | **Mitutoyo M Plan Apo 10X / 378-803-3** | 10×；**NA 0.28**；WD 34.0 mm；f = 20 mm；分辨力 R = 1.0 µm；景深 3.5 µm；视场 Ø2.4 mm（Ø24 目镜）；校正波长 436–656 nm；无限远校正、平场复消色差；M26×36TPI；240 g | Mitutoyo 官方产品表 https://pim.mitutoyo.com/products/optical-measurement/infinity-corrected-microscope-objectives/m-plan-apo-for-brightfield-observation ；官方商城规格页 https://shop.mitutoyo.eu/web/mitutoyo/de_CH/mitutoyo/05.04.02/M%20Plan%20Apo%2010X/$catalogue/mitutoyoData/PR/378-803-3/index.xhtml |
| 5 | 筒镜（图 1 的 Apo，推断） | **Nikon MXA22018**（CFI 第二镜组 / 筒镜） | f = 200 mm；与无限远校正物镜配用，把平行光束会聚到相机靶面；物镜肩后约 100 mm 放置 | BAM 实际搭建论文（ACS J. Phys. Chem. A）https://pubs.acs.org/doi/full/10.1021/acs.jpca.0c05849 ；OSU 学位论文 https://research.cbc.osu.edu/allen.697/wp-content/uploads/2011/09/thesis_castada-8-5-10-v3.pdf |
| 6 | 面阵探测器 | **Basler acA2040-90um**（ace Classic） | ams CMV4000 CMOS，全局快门；**2048×2048**、像元 **5.5×5.5 µm**；1″（11.26×11.26 mm）；90 fps；10/12 bit；QE 62.07% @541 nm；暗噪声 13.8 e⁻；满阱 11.9 ke⁻；动态范围 58.7 dB；SNR 40.8 dB；USB 3.0；C-mount；29.3×29×29 mm、80 g | Basler 官方产品页 https://www.baslerweb.com/en-sg/shop/aca2040-90um/ ；官方文档 https://docs.baslerweb.com/aca2040-90um |
| 7 | Langmuir 槽 / 样品台 | **Biolin KSV NIMA Medium（KN 2002）** | 表面积 273 cm²；内尺寸 364×75×4 mm；PTFE 槽体；双滑障 0.1–270 mm/min（精度 0.1 mm/min）；表面压 0–300 mN/m；天平分辨力 0.1 µN/m；Wilhelmy 铂金板 W19.62×H10 mm（EN 14370:2004）；最大压缩比 10.8；亚相体积 109 mL | Biolin 官方技术规格页 https://www.biolinscientific.com/ksvnima/technical-specifications ；中文代理规格页 http://www.biolin17.com/Products-39024721.html |
| 8 | 精密测角 / 旋转台 | **Newport URS50BPP**（`URS-BPP` 系列）；HWP/GL 定向用 **Thorlabs PRM1Z8** | URS50BPP(V6)：分辨率 0.0014°、最小增量 0.0015°、单向重复性 ±0.002°、绝对精度 ±0.02°、360° 连续；PRM1Z8：最小增量 25 arcsec（≈0.0069°）、可重复增量 0.03°、双向重复性 ±0.1°、主刻度 1° 带游标、360° 连续 | Newport 参数页 https://www.oeshow.cn/mobile/goodsDetail/12100 ；Thorlabs 官方页 https://www.thorlabs.com/motorized-precision-rotation-mount?pn=KPRM1E |
| 9 | 商用 BAM 对标（分辨率指标参照） | **Biolin KSV NIMA MicroBAM**；早期 **KSV OPTREL MicroBAM** | 现行版：入射角固定 53°；光源 659 nm / 50 mW；**图像分辨率 12 µm**（水平方向中心，Rayleigh 判据）；视场 3600×4000 µm；集成起偏器（p 偏振）与检偏器；早期版：He-Ne 633 nm / 10 mW、CCD 640×480、空间分辨率 2 µm、Glan-Thompson 偏振器、固定 53°；两者均注明「因观察角度原因，图像仅聚焦在视场中心」 | Biolin/DKSH 官方规格 https://technology-products.dksh.co.th/th-en/product/biolin-deposition-characterization-thin-films-2 ；早期版参数 https://www.chem17.com/offer_sale/detail/15296371.html 、https://m.antpedia.com/instrument/42968 |

**图 1 缩写 `GL` / `Apo` 的核实结论**：
- `GL` = **Glan-Laser（Glan 型）方解石起偏棱镜**：BAM 文献明确使用「Glan-laser calcite polarizer」（ACS 论文）与 Thorlabs GL10-A（OSU 学位论文），图注缩写与之吻合 → 由「推断」升级为**有文献支撑的确认**，但图 1 未写出全称，文档按「缩写还原」表述。
- `Apo` 仍为**推断**：按无限远校正光路，Obj 之后、探测器之前必须是筒镜（tube lens）；Nikon MXA22018 / 复消色差镜组位于该位置。图 1 未标注全称，文档按「筒镜/复消色差镜组」理解并注明待文献确认。

---

## 二、物理常数与色散数据核实

| 项 | 数值 | 来源 |
|---|---|---|
| 水折射率色散（20.0 °C，HPLC 蒸馏水） | Sellmeier 四系数：`0.5684027565/(λ²−0.005101829712)` 等四项；n(632.8 nm) = **1.332106**；n(587.6 nm) = 1.333402；dn/dλ = −0.031335 µm⁻¹ | M. Daimon, A. Masumura. *Appl. Opt.* **46**(19): 3811–3820 (2007), DOI 10.1364/AO.46.003811；数据页 https://refractiveindex.info/?shelf=main&book=H2O&page=Daimon-20.0C |
| 水折射率温度系数（21.5 °C 对照） | dn/dT ≈ **−9.2×10⁻⁵ /°C**（由 20.0 °C 与 21.5 °C 两组 Sellmeier 在 632.8 nm 处差分） | 同上，21.5 °C 页 https://refractiveindex.info/?shelf=main&book=H2O&page=Daimon-21.5C |
| 空气/水布儒斯特角 | n₂ = 1.33 → **θB ≈ 53.1°**（通用教学值）；文献实测搭建 53.1° | ACS 论文（goniometer 调到 53.1°）；OpenStax/Vaia 教材题 arctan(1.33)=53.1° |
| 布儒斯特条件与 Fresnel 公式 | tanθB = n₂/n₁；r_p、r_s 表达式；p 偏振在 θB 下 r_p = 0 | Born & Wolf *Principles of Optics* 7th ed. §1.5；Hecht *Optics* 5th ed. |

> **口径说明**：`.blend` 建模采用教学基准 n₂ = 1.333（→ θB = 53.1232°），与 Daimon–Masumura 在 632.8 nm / 20 °C 的实测 n = 1.332106（→ 53.1048°）相差 0.0185°。该差值正是第 4 项「波长/温度引起折射率漂移 → 需重新标定入射角」的定量依据，设计文档与仿真均按「建模基准 + 实测修正」双口径给出，不改动已通过 56 项检查的 `.blend` 几何。

---

## 三、BAM 原理 / 应用文献核实（GB/T 7714 著录信息）

| # | 文献 | 核实到的著录信息 | 用途 |
|---|---|---|---|
| [1] | HÖNIG D, MÖBIUS D. Direct visualization of monolayers at the air–water interface by Brewster angle microscopy[J]. **The Journal of Physical Chemistry, 1991, 95(12): 4590–4592.** DOI: 10.1021/j100165a003 | DOI 页 https://explore.openaire.eu/search/publication?pid=10.1021%2Fj100165a003 ；Mendeley https://www.mendeley.com/catalogue/25b163f4-9d35-32a8-9f47-39113365ef2d | BAM 开山论文；p 偏振 θB 下裸界面零反射、成膜后产生反射、反射率–面积等温线 |
| [2] | VOLLHARDT D. Morphology and phase behavior of monolayers[J]. **Advances in Colloid and Interface Science, 1996, 64: 143–171.** DOI: 10.1016/0001-8686(95)00285-5 | CNKI Scholar https://scholar.cnki.net/Detail/index/GARJ8099_1/SJESC009326634D0572D44326B1753C3882E | BAM 是最有效的单分子膜形貌表征手段 |
| [3] | VOLLHARDT D. Mesoscopic characterization of amphiphilic monoglycerol monolayers[J]. **Advances in Colloid and Interface Science, 2018, 258: 36–46.** DOI: 10.1016/j.cis.2018.07.002 | CNGBdb / PubMed 30056937 https://db.cngb.org/data_resources/literature/30056937/ | BAM 高灵敏成像、介观畴结构 |
| [4] | Revisiting the Brewster Angle Microscopy: the relevance of the polar headgroup[J]. **Advances in Colloid and Interface Science, 2012.** DOI: 10.1016/j.cis.2012.02.002, PMID 22397863 | PubMed https://www.pubmed.ncbi.nlm.nih.gov/22397863/ | 膜层极性头基对 BAM 反射率的影响；由图像反演定量结构信息 |
| [5] | Relating Structure and Ice Nucleation of Mixed Surfactant Systems Relevant to Sea Spray Aerosol[J]. **The Journal of Physical Chemistry A, 2020.** DOI: 10.1021/acs.jpca.0c05849 | ACS 全文 https://pubs.acs.org/doi/full/10.1021/acs.jpca.0c05849 | 完整自建 BAM 配置：Glan-laser 起偏、测角仪 53.1°、10× SLWD 物镜 + f=200 mm 筒镜、EM-CCD 512×512/16 µm、Langmuir 槽 Wilhelmy 板 |
| [6] | CASTADA H Z. Brewster Angle Microscopy Study of Model Lung Surfactant Systems…[D]. Columbus: The Ohio State University, 2010. | 全文 https://research.cbc.osu.edu/allen.697/wp-content/uploads/2011/09/thesis_castada-8-5-10-v3.pdf | GL10-A 消光比 100 000:1、Nikon CF Plan EPI 20×/NA 0.35/WD 20.5 mm + MXA22018 筒镜、PRMGL10 旋转座 |
| [7] | DAIMON M, MASUMURA A. Measurement of the refractive index of distilled water from the near-infrared region to the ultraviolet region[J]. **Applied Optics, 2007, 46(19): 3811–3820.** DOI: 10.1364/AO.46.003811 | DOI 页 https://doi.org/10.1364/AO.46.003811 ；https://refractiveindex.info/?shelf=main&book=H2O&page=Daimon-20.0C | 水折射率色散与温度系数，θB 漂移定量 |
| [8] | BORN M, WOLF E. Principles of Optics: Electromagnetic Theory of Propagation, Interference and Diffraction of Light[M]. 7th ed. Cambridge: Cambridge University Press, 1999. ISBN 0521642221. | 图书馆目录 https://science-catalogue.canada.ca/record=b1892414~S6 ；JEOS 参考文献 https://jeos.edpsciences.org/articles/jeos/ref/2025/01/jeos20250013/jeos20250013.html | Fresnel 公式、布儒斯特角、薄膜光学 |
| [9] | HECHT E. Optics[M]. 5th ed. Boston: Pearson, 2017. | JEOS 参考文献（同上） | 偏振、Fresnel、干涉与衍射基础 |

**厂商 / 产品资料（不作为学术文献编号，仅在选型表与台账中引 URL）**：Thorlabs（HNL050L、WPH05M-633、GL10-A、PRM1Z8）、Mitutoyo（378-803-3）、Basler（acA2040-90um）、Biolin Scientific（KSV NIMA、MicroBAM）、Nikon（MXA22018）、Newport（URS-BPP）。

---

## 四、检索中遇到但**未采纳**的信息（避免误用）

- 某 AI 生成百科（Grokipedia）给出「BAM 纵向灵敏度 0.2 nm、入射角精度 0.001°、512×512/24 µm 背照 CCD」等数值，因非一手来源、无法核验，**未写入设计**；分辨率指标改用 MicroBAM 官方规格与 Rayleigh 判据自行推算。
- 百度百科给出「Nanofilm EP3BAM / JB04、偏振比 10⁻⁸、1360×1024 CCD」等，与厂商现行参数不一致，仅作背景了解，**不引用**。
- 第三方经销商页面的 MicroBAM 分辨率（2 µm）与厂商现行规格（12 µm）冲突，已按版本区分表述，未混用。
