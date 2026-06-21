# -*- coding: utf-8 -*-
# @Time    : 2026/3/24 
# @File    : f10_parser.py
# @Project : Alkaid-main
# @Author  : Chiang Tao
# @Version : 0.1.00
"""
F10 数据解析器（增强版）
基于港澳资讯格式，整合旧版成功提取逻辑，确保基本资料字段正确提取。
关联企业部分增加健壮的表格解析和回退方案。
"""
"""
- 基本资料：基于表格字段提取（已稳定）
- 发行上市：基于表格字段提取（已稳定）
- 关联企业：独立模块，支持带线条表格及跨行合并
"""

import re
from typing import Dict, Any, List, Optional
import pandas as pd
from loguru import logger


class F10Parser:
    def __init__(self, text: str, debug: bool = False):
        self.raw = text
        self.debug = debug
        self.sections = self._split_sections()

    def _split_sections(self) -> Dict[str, str]:
        pattern = r'【(\d+\.\S+)】'
        matches = list(re.finditer(pattern, self.raw))
        sections = {}
        for i, match in enumerate(matches):
            title = match.group(1)
            start = match.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(self.raw)
            content = self.raw[start:end].strip()
            sections[title] = content
        if self.debug:
            logger.debug(f"解析到章节: {list(sections.keys())}")
        return sections

    # ===================== 基本资料提取 =====================
    def _extract_table_field(self, text: str, field_name: str) -> str:
        pattern = rf'{field_name}\s*[｜|]\s*(.*?)(?=\s*[｜|]|\n|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            value = match.group(1).strip()
            parts = re.split(r'[｜|]', value)
            return parts[0].strip()
        return "未提取到"

    def _extract_paragraph(self, text: str, title: str) -> str:
        patterns = [
            rf'★{title}★\s*(.*?)(?=\n\s*★|\n\n|$)',
            rf'【{title}】\s*(.*?)(?=\n\s*【|\n\n|$)',
            rf'{title}[：:]\s*(.*?)(?=\n\s*[A-Za-z\u4e00-\u9fa5]+[：:]|\n\n|$)',
            rf'^{title}\s*(.*?)(?=\n\s*[★【]|\n\n|$)',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return "未提取到"

    def _parse_basic_info(self, content: str) -> Dict[str, Any]:
        key_fields = {
            "公司名称": ["公司名称"],
            "英文名称": ["英文名称"],
            "证券代码": ["证券代码"],
            "行业类别": ["行业类别", "所属行业"],
            "上市日期": ["上市日期"],
            "注册资本": ["注册资本"],
            "法人代表": ["法定代表人", "法人代表"],
            "注册地址": ["注册地址"],
            "办公地址": ["办公地址"],
            "主营业务": ["主营业务"],
            "经营范围": ["经营范围"],
            "公司简介": ["公司简介", "★公司简介★", "【公司简介】"],
        }
        result = {}
        for display_name, search_keys in key_fields.items():
            for sk in search_keys:
                value = self._extract_table_field(content, sk)
                if value != "未提取到":
                    result[display_name] = value
                    break
            else:
                if display_name in ["主营业务", "经营范围", "公司简介"]:
                    value = self._extract_paragraph(content, display_name)
                    if value != "未提取到":
                        result[display_name] = value
        return result

    # ===================== 发行上市 =====================
    def _parse_listing_info(self, content: str) -> Dict[str, Any]:
        key_fields = {
            "网上发行日期": ["网上发行日期"],
            "上市日期": ["上市日期"],
            "发行方式": ["发行方式"],
            "发行量(股)": ["发行量(股)"],
            "每股发行价(元)": ["每股发行价(元)"],
            "募集资金净额(元)": ["募集资金净额(元)"],
            "上市首日收盘价(元)": ["上市首日收盘价(元)"],
            "主承销商": ["主承销商"],
            "保荐人": ["保荐人"],
        }
        result = {}
        for display_name, search_keys in key_fields.items():
            for sk in search_keys:
                value = self._extract_table_field(content, sk)
                if value != "未提取到":
                    result[display_name] = value
                    break
        return result

    # ===================== 关联企业解析（独立模块） =====================
    def _parse_affiliated_companies(self, content: str) -> Dict[str, Any]:
        """解析关联企业表格，返回结构化数据"""
        return AffiliatedCompaniesParser(content, debug=self.debug).parse()

    # ===================== 主解析入口 =====================
    def parse(self) -> Dict[str, Any]:
        result = {
            'basic_info': {},
            'listing_info': {},
            'affiliated_companies': {},
            'other_sections': {}
        }
        for title, content in self.sections.items():
            if title.startswith('1.基本资料'):
                result['basic_info'] = self._parse_basic_info(content)
            elif title.startswith('2.发行上市'):
                result['listing_info'] = self._parse_listing_info(content)
            elif title.startswith('4.关联企业'):
                result['affiliated_companies'] = self._parse_affiliated_companies(content)
            else:
                result['other_sections'][title] = content
        return result

    def extract_main_info(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        main = {}
        main.update(parsed.get('basic_info', {}))
        main.update(parsed.get('listing_info', {}))
        aff = parsed.get('affiliated_companies', {})
        main['关联企业数量'] = aff.get('total_count', 0)
        main['关联企业日期'] = aff.get('date')
        main['关联关系分布'] = aff.get('by_relationship', {})
        main['投资情况'] = aff.get('investment_summary', {})
        return main


class AffiliatedCompaniesParser:
    """关联企业表格解析器（独立，便于测试）"""

    def __init__(self, content: str, debug: bool = False):
        self.content = content
        self.debug = debug

    def parse(self) -> Dict[str, Any]:
        """主入口，返回解析结果"""
        # 提取日期和总数
        date_match = re.search(r'截止日期[：:]\s*(\d{4}-\d{2}-\d{2})', self.content)
        count_match = re.search(r'共(\d+)家', self.content)
        summary = {
            'date': date_match.group(1) if date_match else None,
            'total_count': int(count_match.group(1)) if count_match else 0,
        }

        if self.debug:
            logger.debug(f"关联企业截止日期: {summary['date']}, 总数: {summary['total_count']}")
            logger.debug(f"关联企业内容前500字符:\n{self.content[:500]}")

        # 提取表格数据
        tables = self._extract_table()
        if not tables:
            if self.debug:
                logger.warning("关联企业表格提取失败，使用回退方案")
            summary['by_relationship'] = self._extract_relationships_from_text()
            summary['by_business'] = {}
            summary['investment_summary'] = {
                'has_begin_investment': 0, 'no_begin_investment': 0,
                'has_end_investment': 0, 'no_end_investment': 0,
            }
            summary['companies'] = []
            return summary

        # 转换为 DataFrame 并统计
        df = pd.DataFrame(tables)
        # 列名标准化
        col_map = {
            '截止日期': 'report_date',
            '关联方名称': 'company_name',
            '关联关系': 'relationship',
            '所占比例(％)': 'ownership_pct',
            '投资期初余额(元)': 'investment_begin',
            '投资期末余额(元)': 'investment_end',
            '主营业务': 'business',
        }
        for old, new in col_map.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)

        # 清理数值列
        for col in ['ownership_pct', 'investment_begin', 'investment_end']:
            if col in df.columns:
                df[col] = df[col].replace('-', pd.NA).replace('', pd.NA)
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 统计
        by_relationship = df['relationship'].value_counts().to_dict() if 'relationship' in df.columns else {}
        by_business = {}
        if 'business' in df.columns:
            df['business_clean'] = df['business'].str.replace(r'\s+', ' ', regex=True).str.strip()
            by_business = df['business_clean'].value_counts().to_dict()

        investment_summary = {
            'has_begin_investment': int(df['investment_begin'].notna().sum()) if 'investment_begin' in df.columns else 0,
            'no_begin_investment': int(df['investment_begin'].isna().sum()) if 'investment_begin' in df.columns else 0,
            'has_end_investment': int(df['investment_end'].notna().sum()) if 'investment_end' in df.columns else 0,
            'no_end_investment': int(df['investment_end'].isna().sum()) if 'investment_end' in df.columns else 0,
        }

        summary.update({
            'companies': df.to_dict('records'),
            'by_relationship': by_relationship,
            'by_business': by_business,
            'investment_summary': investment_summary,
        })
        return summary

    def _extract_table(self) -> List[Dict[str, str]]:
        """提取表格数据，优先使用带合并的线条表格解析"""
        # 方法1：带合并的线条表格
        data = self._extract_line_table_merge()
        if data:
            return data
        # 方法2：普通线条表格
        data = self._extract_line_table()
        if data:
            return data
        # 方法3：纯文本表格
        return self._extract_pipe_table()

    def _extract_line_table_merge(self) -> List[Dict[str, str]]:
        """解析带线条表格并处理跨行合并"""
        lines = self.content.split('\n')
        start, end = None, None
        for i, line in enumerate(lines):
            if re.match(r'┌[─┬┐]*┐', line):
                start = i
            elif re.match(r'└[─┴┘]*┘', line):
                end = i
                break
        if start is None or end is None:
            return []

        # 找表头行
        header_line = None
        for i in range(start+1, end):
            line = lines[i].strip()
            if not line or line.startswith('├') or line.startswith('└'):
                continue
            if '│' in line:
                header_line = i
                break
        if header_line is None:
            return []

        # 解析表头
        header_cells = [cell.strip() for cell in lines[header_line].split('│')[1:-1]]
        data = []
        current_row = None
        current_row_cells = []

        for i in range(header_line+1, end):
            line = lines[i].strip()
            if not line:
                continue
            if line.startswith('├') or line.startswith('└'):
                # 分割线，保存当前行
                if current_row is not None:
                    data.append(current_row)
                    current_row = None
                    current_row_cells = []
                continue

            # 数据行
            cells = [cell.strip() for cell in line.split('│')[1:-1]]
            if not cells:
                continue

            # 判断是否为新行：单元格数量等于表头数量 或 当前无活跃行
            if current_row is None or len(cells) == len(header_cells):
                if current_row is not None:
                    data.append(current_row)
                current_row = {}
                current_row_cells = cells[:]
                for j, cell in enumerate(current_row_cells):
                    if j < len(header_cells):
                        current_row[header_cells[j]] = cell
            else:
                # 跨行合并：将当前单元格附加到上一行对应列
                for j, cell in enumerate(cells):
                    if j < len(header_cells):
                        col = header_cells[j]
                        if col in current_row:
                            current_row[col] += '\n' + cell
                        else:
                            current_row[col] = cell
                current_row_cells = cells[:]

        if current_row is not None:
            data.append(current_row)

        return data

    def _extract_line_table(self) -> List[Dict[str, str]]:
        """普通线条表格解析（不处理合并）"""
        lines = self.content.split('\n')
        start, end = None, None
        for i, line in enumerate(lines):
            if re.match(r'┌[─┬┐]*┐', line):
                start = i
            elif re.match(r'└[─┴┘]*┘', line):
                end = i
                break
        if start is None or end is None:
            return []

        header_line = None
        for i in range(start+1, end):
            line = lines[i].strip()
            if not line or line.startswith('├') or line.startswith('└'):
                continue
            if '│' in line:
                header_line = i
                break
        if header_line is None:
            return []

        header_cells = [cell.strip() for cell in lines[header_line].split('│')[1:-1]]
        data = []
        for i in range(header_line+1, end):
            line = lines[i].strip()
            if not line or line.startswith('├') or line.startswith('└'):
                continue
            cells = [cell.strip() for cell in line.split('│')[1:-1]]
            if len(cells) != len(header_cells):
                continue
            row = {header_cells[j]: cells[j] for j in range(len(header_cells))}
            data.append(row)
        return data

    def _extract_pipe_table(self) -> List[Dict[str, str]]:
        """纯文本表格解析"""
        lines = self.content.split('\n')
        table_lines = [line for line in lines if '|' in line]
        if len(table_lines) < 2:
            return []
        header_line = table_lines[0]
        headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
        if not headers:
            return []
        data = []
        for line in table_lines[1:]:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) != len(headers):
                continue
            row = {headers[j]: cells[j] for j in range(len(headers))}
            data.append(row)
        return data

    def _extract_relationships_from_text(self) -> Dict[str, int]:
        """回退方案：关键词统计"""
        rel_keywords = ['子公司', '控股股东', '实际控制人', '联营企业', '合营企业', '参股公司']
        results = {}
        for kw in rel_keywords:
            count = len(re.findall(kw, self.content))
            if count > 0:
                results[kw] = count
        return results