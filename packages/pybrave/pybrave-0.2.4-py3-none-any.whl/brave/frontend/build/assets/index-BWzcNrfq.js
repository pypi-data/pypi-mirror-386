import{j as t,B as r,d as o}from"./main-CH82g4dw.js";import{A as n}from"./index-qh3iVWpI.js";import{T as a}from"./index-CweiUdAw.js";import{T as m}from"./index-B_L60N4-.js";import"./index-BA3Y6Ju-.js";import"./index-6IaXHF5K.js";import"./index-BcI8WOZ3.js";import"./Dropdown-B4TP4OlU.js";import"./Table-Rz-gL0vt.js";import"./addEventListener-DrXUXNAy.js";import"./index-BL_XwOQI.js";import"./index-C0dVCwMu.js";import"./index-DOFo5PXu.js";import"./index-Pwpmen_B.js";import"./createForOfIteratorHelper-BSFJLzX3.js";import"./DeploymentUnitOutlined-WBguncE1.js";import"./UserSwitchOutlined-D2V22kEV.js";import"./AudioOutlined-Cdmej0V0.js";import"./ClearOutlined-CzC8yyS0.js";import"./DeleteOutlined-CIV_DNOf.js";import"./TableOutlined-CZ_BS3k3.js";import"./NodeIndexOutlined-Cav4TyHH.js";import"./index-DTJd4Z3p.js";import"./RedoOutlined-DNpCn5kL.js";import"./UndoOutlined-BfseYVP6.js";import"./UpOutlined-MKfWXv9S.js";import"./react-window-Bmvezp4W.js";import"./index-L_EWe7Ii.js";import"./index-B1-7HnQ_.js";import"./index-ZaXfouA1.js";import"./index-_r2zE_l-.js";import"./index-Cem7jUqj.js";import"./callSuper-wDHXj85E.js";import"./index-DgI-8QMg.js";import"./index-egZsYIid.js";import"./index-BKAfqOdf.js";import"./index-DH4f004y.js";import"./index-B6FNwvkQ.js";import"./index-BtlAu1CQ.js";import"./index-BXUynQ4Q.js";import"./index-D4N7VkC-.js";import"./study-page-CyTzU1IC.js";import"./usePagination-CNS7-0k1.js";import"./index-DqMpSPzc.js";import"./index-BDU4gvFg.js";import"./index-BkCTNNpG.js";import"./panel-DJNmOhc6.js";import"./index-CXizBL-u.js";const p=({record:i,plot:e})=>t.jsx(t.Fragment,{children:i?t.jsxs(t.Fragment,{children:[t.jsx(r,{onClick:()=>{e({name:"基因预测统计",saveAnalysisMethod:"prokka_txt_plot",moduleName:"prokka_txt_plot",params:{file_path:i.content.txt}})},children:"基因预测统计"}),t.jsx(r,{onClick:()=>{e({moduleName:"genome_circos_plot_gbk",params:{file_path:i.content.gbk},tableDesc:`
+ GC skew 是一个用来衡量 DNA 序列中 鸟嘌呤（G）和胞嘧啶（C）含量不对称性 的指标，常用于分析细菌基因组的复制起点（oriC）和终点（terC）。
+ GC skew 通常定义为：
$$
GC skew=\\frac{G - C}{G + C}
$$
+ G：一个窗口内 G 的数量
+ C：一个窗口内 C 的数量
+ 值范围：[-1, 1]，值越大表示 G 多于 C，反之亦然。
+ 在基因组图上的意义
    + 在原核生物（如大肠杆菌）中，GC skew 通常沿着基因组有明显的变化。
    + 常用于推测复制起点（origin of replication，ori）和终点（terminus，ter）的位置。
        + ori 附近 GC skew 通常从负变正
        + ter 附近则从正变负


                `})},children:"基因组圈图(gbk)"}),t.jsx(r,{onClick:()=>{e({moduleName:"genome_circos_plot_gff",params:{file_path:i.content.gff}})},children:"基因组圈图(gff)"}),t.jsx(r,{onClick:()=>{e({moduleName:"dna_features_viewer_gbk",params:{file_path:i.content.gbk},formDom:t.jsxs(t.Fragment,{children:[t.jsx(o.Item,{label:"REGION_START ",name:"REGION_START",initialValue:1e3,children:t.jsx(a,{})}),t.jsx(o.Item,{label:"REGION_END ",name:"REGION_END",initialValue:1e4,children:t.jsx(a,{})})]}),tableDesc:`
## 关于基因名称注释
+ gff文件
    + 	1522	2661
    + positive strand
    + ID=PPIEBLPA_00002;
    + Name=dnaN;
    + db_xref=COG:COG0592;
    + gene=dnaN;
    + inference=ab initio prediction:Prodigal:002006,similar to AA sequence:UniProtKB:P05649;
    + locus_tag=PPIEBLPA_00002;
    + product=Beta sliding clamp
+ gkb文件
    + CDS
    +  /gene="dnaN"
    + /locus_tag="PPIEBLPA_00002"
    + /inference="ab initio prediction:Prodigal:002006"
    + /inference="similar to AA sequence:UniProtKB:P05649"
    + /codon_start=1
    + /transl_table=11
    + /product="Beta sliding clamp"
    + /db_xref="COG:COG0592"
    + /translation="MKFTVHRTAFIQYLNDVQRAI...PVRTV"
+ gff文件
    + 1576703	1577125	
    + positive strand
    + ID=PPIEBLPA_01577;
    + inference=ab initio prediction:Prodigal:002006;
    + locus_tag=PPIEBLPA_01577;
    + product=hypothetical protein
+ gkb文件
    + CDS             
    + 1576703..1577125
    + /locus_tag="PPIEBLPA_01577"
    + /inference="ab initio prediction:Prodigal:002006"
    + /codon_start=1
    + /transl_table=11
    + /product="hypothetical protein"
    + /translation="MSNDYRNSEGYPDPTAG...RYFTEECQEV"
                `})},children:" 基因组区域基因(gbk)"}),t.jsx(r,{onClick:()=>{e({name:"prokka初步功能注释",saveAnalysisMethod:"prokka_annotation",moduleName:"prokka_annotation",params:{file_path:i.content.tsv},tableDesc:`
                `})},children:" prokka初步功能注释"})]}):t.jsx(t.Fragment,{children:t.jsx("p",{children:"选择一个样本开始分析"})})}),rt=()=>t.jsxs(t.Fragment,{children:[t.jsx(m,{items:[{key:"Prokka",label:"Prokka",children:t.jsx(t.Fragment,{children:t.jsx(n,{inputAnalysisMethod:[{name:"1",label:"基因组组装文件",inputKey:["ngs-individual-assembly","tgs_individual_assembly"],mode:"multiple",type:"GroupSelectSampleButton",groupField:"sample_group",rules:[{required:!0,message:"该字段不能为空!"}]}],analysisMethod:[{name:"1",label:"prokka",inputKey:["prokka"],mode:"multiple"}],analysisType:"sample",children:t.jsx(p,{})})})}]}),t.jsx("p",{})]});export{rt as default};
