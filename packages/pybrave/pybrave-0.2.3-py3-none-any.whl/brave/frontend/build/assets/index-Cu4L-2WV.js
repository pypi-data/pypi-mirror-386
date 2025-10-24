import{r as m,j as e,B as n,d as _,e as d,a as g}from"./main-D6qHus43.js";import{A as h}from"./index-1laYOQoJ.js";import{f}from"./utils-D2B0dIuM.js";import{T as c}from"./index-gg_8jVgT.js";import"./index-CXgqoLfI.js";import"./index-CjmxhRai.js";import"./index-DOQLu3Xz.js";import"./index-CqzThpCE.js";import"./UpOutlined-DC7OgFJP.js";import"./DeleteOutlined-5gHEV1Sl.js";import"./index-BLl0dAbY.js";import"./Dropdown-CMUlroR_.js";import"./Table-Pcm8h2F_.js";import"./addEventListener-TTc5ki3v.js";import"./index-CScjzpru.js";import"./index-DUjGi303.js";import"./createForOfIteratorHelper-Cwfr5VEp.js";import"./DeploymentUnitOutlined-Bm7mxWYi.js";import"./UserSwitchOutlined-DxcFBqrp.js";import"./AudioOutlined-CPyhrC5-.js";import"./ClearOutlined-sPRC32yu.js";import"./TableOutlined-CS-DfnXV.js";import"./NodeIndexOutlined-GDqggOsJ.js";import"./RedoOutlined-DIIHLGCK.js";import"./UndoOutlined-CVmeWyj0.js";import"./react-window-CDDJu4Rx.js";import"./index-D7dvcYwa.js";import"./index-CoiYZhLe.js";import"./index-CYPnvC5G.js";import"./index-CkLVmzff.js";import"./index-oyOmkC6S.js";import"./index-WNIwdokR.js";import"./index-D0Z8XcmH.js";import"./index-CSAVJvIu.js";import"./study-page-CTl0wbzh.js";import"./usePagination-C3C4V5nb.js";import"./index-C4HNXQqg.js";import"./index-ChzQGd2Q.js";import"./index-DyK7Pyu1.js";import"./callSuper-BOdF8PPo.js";import"./index-DjsvXEZy.js";import"./index-DIOsMt1p.js";import"./rgb-BwIoVOhg.js";import"./index-ytJ9UBRy.js";const y=({record:t,plot:a,setHtmlUrl:u,cleanDom:o,resultTableList:r,form:p})=>{const[l,i]=m.useState();return e.jsx(e.Fragment,{children:e.jsx(c,{onChange:o,items:[{key:"1",label:"多样本分析",children:e.jsxs(e.Fragment,{children:[e.jsx(n,{type:"primary",onClick:()=>{a({saveAnalysisMethod:"mutations_gene",moduleName:"circos_plot_mutations",params:{file_path:"/ssd1/wy/workspace2/leipu/leipu_workspace2/output/breseq/OSP-6/data/OSP-6.count"},formDom:e.jsx(e.Fragment,{children:e.jsx(_.Item,{name:"list_files",label:"选择样本",children:e.jsx(d,{mode:"multiple",style:{maxWidth:"20rem"},allowClear:!0,options:r.breseq?r.breseq.map(s=>({label:`${s.sample_name} (${s.content.reference})`,value:`${s.sample_name}#${s.content.annotated_tsv}`})):[]})})}),tableDesc:`
+ 选择样本说明:
    + 下拉框样本的命名格式为: 样本名 (参考基因组)

                                `})},children:"基因突变圈图"}),e.jsx(n,{type:"primary",onClick:()=>{a({sampleGroupJSON:!0,formJson:[{name:"genome",label:"基因组",rules:[{required:!0,message:"该字段不能为空!"}],type:"FilterFieldSelect",field:s=>s.content.reference,clear:["sites"]},{name:"group_field",label:"分组列",rules:[{required:!0,message:"该字段不能为空!"}],type:"GroupFieldSelect"},{name:"sites",label:"部位",rules:[{required:!0,message:"该字段不能为空!"}],type:"GroupSelectSampleButton",group:"group_field",filter:[{name:"genome",method:s=>s.content.reference}]}],sampleGroupApI:!1,saveAnalysisMethod:"snv_phylogenetic_tree",moduleName:"snv_phylogenetic_tree",sampleSelectComp:!1,tableDesc:" ",name:"基于SNV系统发育树"})},children:"基于SNV系统发育树"})]})},{key:"2",label:e.jsxs(e.Fragment,{children:["单样本分析(",t&&e.jsxs(e.Fragment,{children:[t==null?void 0:t.analysis_name,"-",t==null?void 0:t.sample_name]}),")"]}),disabled:!t,children:e.jsxs(e.Fragment,{children:[e.jsx(n,{onClick:()=>{a({url:f(t.content.index_html),tableDesc:`
+ [结果说明文档](https://gensoft.pasteur.fr/docs/breseq/0.35.0/output.html#html-human-readable-output)

![](https://gensoft.pasteur.fr/docs/breseq/0.35.0/_images/snp_2.png)
> 在 ychE 和 oppA 基因之间的基因间区域，用一个 G 替换了位于 1,298,712 位的参考 T。该基因突变在 ychE 的下游 674 个碱基（因为该基因的位置在 ychE 之前，且在参考文献的顶链上），在 oppA 的上游 64 个碱基（因为该基因的位置在 oppA 之后，且也在基因组的顶链上）。                        `})},children:"查看报告"}),e.jsx(n,{onClick:()=>{a({moduleName:"tsv",params:{file_path:t.content.annotated_tsv},tableDesc:`
## locus_tag的解释(OSI-5为例)
+ 对于gyrB/gyrA、PPIEBLPA_00087/PPIEBLPA_00088, 这类locus_tag对应的mutation_category包括
    + snp_intergenic: snp位点发生在基因间区，/ 前的两个基因代表突变位点的上游和下游的基因
    + small_indel: indel位点发生在基因间区，/ 前的两个基因代表突变位点的上游和下游的基因        
    + large_deletion: large deletion位点发生在基因间区，/ 前的两个基因代表突变位点的上游和下游的基因      
+ 对于PPIEBLPA_01703|PPIEBLPA_01704，突变位点1711867同时发生在两个基因上
    + rhaR_2: 1711442	1711870
    + malL_1: 1711861	1713489                             
+ 对于[PPIEBLPA_00342]–[PPIEBLPA_00343]代表large deletion跨越了两个基因
+ 对于[PPIEBLPA_00863]代表large deletion发生在基因区，以及该基因的基因间区

> 在分析中可以使用df.query("~locus_tag.str.contains('/') & ~locus_tag.str.contains('[') & ~locus_tag.str.contains('|') & ~locus_tag.str.contains('–')")将上述locus_tag排除,
这样做方便将新的基因注释结果与变异位点相匹配。

## 字段解释

| 字段                                           | 含义                                         |
| -------------------------------------------- | ------------------------------------------ |
| "type": "SNP"                              | 变异类型为单碱基突变（Single Nucleotide Polymorphism） |
| "position": 18936                          | 突变在参考序列上的位置（从1开始）                          |
| "ref_seq": "G"                             | 参考基因组中的碱基是 G                               |
| "new_seq": "T"                             | 变异后读到的是 T                                  |
| "snp_type": "nonsynonymous"                | 非同义突变（导致氨基酸改变）                             |
| "gene_name": "rplI"                        | 受影响的基因名称                                   |
| "gene_product": "50S ribosomal protein L9" | 基因对应的蛋白产品                                  |
| "gene_position": "196"                     | 变异在基因内的位置（碱基坐标）                            |
| "gene_strand": ">"                         | 基因所在链为正链                                   |
| "codon_ref_seq": "GTC"                     | 参考密码子（突变前）为 GTC（编码 Val）                    |
| "codon_new_seq": "TTC"                     | 突变后密码子为 TTC（编码 Phe）                        |
| "aa_ref_seq": "V"                          | 原氨基酸是 V（Val）                               |
| "aa_new_seq": "F"                          | 突变后为 F（Phe）                                |
| "aa_position": "66"                        | 受影响的氨基酸位置是第 66 个                           |
| "codon_number": "66"                       | 对应第 66 个密码子                                |
| "codon_position": "1"                      | 突变发生在密码子的第1位（G→T）                          |
| "mutation_category": "snp_nonsynonymous"   | 更详细的突变分类                                   |
| "locus_tag": "PPIEBLPA_00018"              | 对应注释中的 locus tag                           |
| "locus_tags_overlapping": "PPIEBLPA_00018" | 与该突变重叠的 locus                              |
| "new_read_count": 661                     | 支持新突变的测序读数数目                               |
| "ref_read_count": 0                        | 支持参考序列的读数数量（说明突变已固定或非常纯）                   |
| "seq_id": "Chr"                            | 突变发生在哪条序列上（例如染色体或质粒）                       |
                `})},children:"查看表格"}),e.jsx(n,{onClick:()=>{a({moduleName:"breseq_statistic",params:{file_path:t.content.annotated_count},tableDesc:`
                `})},children:"变异统计"})]})}]})})},me=()=>{const[t,a]=m.useState([]),[u,o]=m.useState(!1),r=async()=>{o(!0);const l=await g.get("/api/mutation");console.log(l),o(!1),a(l.data)};m.useEffect(()=>{r()},[]);const p=[{title:"参考基因组",dataIndex:"reference",key:"reference",ellipsis:!0,render:(l,i)=>{var s;return e.jsx(e.Fragment,{children:(s=i==null?void 0:i.content)==null?void 0:s.reference})}}];return e.jsx(e.Fragment,{children:e.jsx(c,{items:[{label:"breseq",key:"breseq",children:e.jsx(h,{appendSampleColumns:p,analysisMethod:[{name:"breseq",label:"breseq",inputKey:["breseq"],mode:"multiple"}],analysisType:"sample",children:e.jsx(y,{})})}]})})};export{me as default};
