import{j as o,B as i}from"./main-CH82g4dw.js";import{A as r}from"./index-qh3iVWpI.js";import{T as m}from"./index-B_L60N4-.js";import"./index-BA3Y6Ju-.js";import"./index-6IaXHF5K.js";import"./index-BcI8WOZ3.js";import"./Dropdown-B4TP4OlU.js";import"./Table-Rz-gL0vt.js";import"./addEventListener-DrXUXNAy.js";import"./index-BL_XwOQI.js";import"./index-C0dVCwMu.js";import"./index-DOFo5PXu.js";import"./index-CweiUdAw.js";import"./UpOutlined-MKfWXv9S.js";import"./DeleteOutlined-CIV_DNOf.js";import"./index-Pwpmen_B.js";import"./createForOfIteratorHelper-BSFJLzX3.js";import"./DeploymentUnitOutlined-WBguncE1.js";import"./UserSwitchOutlined-D2V22kEV.js";import"./AudioOutlined-Cdmej0V0.js";import"./ClearOutlined-CzC8yyS0.js";import"./TableOutlined-CZ_BS3k3.js";import"./NodeIndexOutlined-Cav4TyHH.js";import"./index-DTJd4Z3p.js";import"./RedoOutlined-DNpCn5kL.js";import"./UndoOutlined-BfseYVP6.js";import"./react-window-Bmvezp4W.js";import"./index-L_EWe7Ii.js";import"./index-B1-7HnQ_.js";import"./index-ZaXfouA1.js";import"./index-_r2zE_l-.js";import"./index-Cem7jUqj.js";import"./callSuper-wDHXj85E.js";import"./index-DgI-8QMg.js";import"./index-egZsYIid.js";import"./index-BKAfqOdf.js";import"./index-DH4f004y.js";import"./index-B6FNwvkQ.js";import"./index-BtlAu1CQ.js";import"./index-BXUynQ4Q.js";import"./index-D4N7VkC-.js";import"./study-page-CyTzU1IC.js";import"./usePagination-CNS7-0k1.js";import"./index-DqMpSPzc.js";import"./index-BDU4gvFg.js";import"./index-BkCTNNpG.js";import"./panel-DJNmOhc6.js";import"./index-CXizBL-u.js";const n=({record:t,plot:e})=>o.jsx(o.Fragment,{children:t&&o.jsxs(o.Fragment,{children:[o.jsx(i,{type:"primary",onClick:()=>{e({name:"查看注释结果",saveAnalysisMethod:"print_gggnog",moduleName:"eggnog",params:{file_path:t.content.annotations,input_faa:t.content.input_faa},tableDesc:`
| 列                      | 含义                                 |
| ---------------------- | ---------------------------------- |
| #query                 | 查询序列的 ID                           |
| seed_eggNOG_ortholog | 种子同源物（最匹配的 EggNOG 同源群）             |
| seed_ortholog_evalue | 种子同源物的比对 E 值                       |
| seed_ortholog_score  | 比对分数                               |
| eggNOG_OGs            | 所属的 EggNOG 同源群（多个可能）               |
| max_annot_lvl        | 最大注释等级（例如 arCOG, COG, NOG 等）       |
| COG_category          | 功能分类（一个或多个字母，详见 EggNOG 分类）         |
| Preferred_name        | 推荐的基因名称                            |
| GOs                    | GO（Gene Ontology）注释                |
| EC                     | 酶编号（Enzyme Commission number）      |
| KEGG_ko               | KEGG 通路编号                          |
| KEGG_Pathway          | KEGG 所属路径                          |
| KEGG_Module           | KEGG 功能模块                          |
| KEGG_Reaction         | KEGG 化学反应编号                        |
| KEGG_rclass           | KEGG 反应类别                          |
| BRITE                  | KEGG BRITE 分类信息                    |
| KEGG_TC               | KEGG Transporter Classification 编号 |
| CAZy                   | 碳水化合物活性酶分类                         |
| BiGG_Reaction         | BiGG 化学反应编号                        |
| PFAMs                  | 蛋白结构域信息（来自 Pfam 数据库）               |

                    `})},children:" 查看注释结果"}),o.jsx(i,{type:"primary",onClick:()=>{e({saveAnalysisMethod:"eggnog_kegg_table",moduleName:"eggnog_kegg",params:{file_path:t.content.annotations},tableDesc:`
                    `,name:"提取KEGG注释结果"})},children:"提取KEGG注释结果"})]})}),to=()=>o.jsxs(o.Fragment,{children:[o.jsx(m,{items:[{key:"eggnog",label:"eggnog",children:o.jsx(o.Fragment,{children:o.jsx(r,{analysisMethod:[{name:"eggnog",label:"eggnog",inputKey:["eggnog"],mode:"multiple"}],analysisType:"sample",children:o.jsx(n,{})})})}]}),o.jsx("p",{})]});export{to as default};
