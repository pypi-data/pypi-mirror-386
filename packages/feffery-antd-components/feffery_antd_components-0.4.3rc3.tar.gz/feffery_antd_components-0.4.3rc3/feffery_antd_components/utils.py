import dash
import warnings
import importlib
from collections import defaultdict
import feffery_antd_components as fac
from typing import Union, Literal, Any, List, Callable, Dict

try:
    import pandas as pd
except ImportError:
    warning_message = (
        '检测到您的环境中未安装\033[93mpandas\033[0m，'
        '部分工具函数如\033[93mdf2table\033[0m将无法正常使用，'
        '如有需要请使用pip或conda安装pandas。'
        '\n\nDetected that \033[93mpandas\033[0m is not installed in your environment. '
        'Some utility functions, such as \033[93mdf2table\033[0m, will not function properly. '
        'If necessary, please install pandas using pip or conda.'
    )
    warnings.warn(warning_message, UserWarning)


__all__ = ['fill_output_dict', 'df2table']


def fill_output_dict(
    output_dict: dict, fill_value: Any = dash.no_update
) -> dict:
    """用于配合回调函数中Output角色的字典化写法，在已有明确字典返回值的基础上，为其他返回项进行默认值填充

    Args:
        output_dict (dict): 已有明确返回值字典
        fill_value (Any): 设置其余无明确返回值的Output角色键值对统一填充值，默认为dash.no_update

    Returns:
        dict: 处理后可以直接通过回调返回的完整Output结果字典
    """

    # 构造辅助用defaultdict
    output = defaultdict(lambda: fill_value, output_dict)

    return {
        key: output[key]
        # 通过上下文遍历所有Output字典键名
        for key in dash.ctx.outputs_grouping.keys()
    }


def df2table(
    raw_df: Any,
    id: str = None,  # 设置对应AntdTable组件的id
    columns_alias: dict = None,  # 为指定字段定义充当title的别名
    # 为指定字段设置对应AntdTable原columns.*.renderOptions配置参数
    columns_render_options: dict = None,
    # 样式相关参数
    # 列宽分配策略，可选的有'auto'、'fmit-title'、'equal'
    column_width_mode: Literal[
        'auto', 'fit-title', 'equal'
    ] = 'auto',
    column_width_sum: str = '100%',  # 用于定义各列宽之和，常用的有'100%'、'1000px'等符合css中宽度规则的值
    left_fixed_columns: List[
        str
    ] = None,  # 定义需要在左侧固定的列名数组
    right_fixed_columns: List[
        str
    ] = None,  # 定义需要在右侧固定的列名数组
    # 字段排序功能相关参数
    numeric_auto_sort: bool = True,  # 是否针对数据框中的数值型字段自动添加排序功能
    # 针对字段排序配置组合排序相关参数，同AntdTable的sortOptions.multiple
    sort_multiple: Union[bool, Literal['auto']] = False,
    # 字段筛选功能相关参数
    str_auto_filter: bool = True,  # 是否针对数据框中的字符型字段自动添加筛选功能
    str_max_unique_value_count: int = 20,  # 允许自动添加筛选功能的字符型字段唯一值数量上限
    checkbox_filter_radio_columns: List[
        str
    ] = None,  # 需要将筛选功能设置为单选模式的字段名数组
    checkbox_filter_enable_search: bool = True,  # 是否为字段筛选菜单启用搜索框
    # 字段编辑功能相关参数
    # 设置需要开启可编辑功能的列名数组，特别地，传入'*'表示全部字段均开启可编辑功能
    editable_columns: Union[List[str], Literal['*']] = None,
    # 数据预处理相关参数
    # 为指定字段设置小数保留位数，特别地，当传入{'*': 小数位数}时，表示对所有数值型字段统一设置保留位数
    columns_precision: dict = None,
    columns_processor: Dict[
        str, Callable
    ] = None,  # 对指定字段进行预处理的自定义函数
    **kwargs,
) -> fac.AntdTable:
    """
    将 pandas DataFrame 转换为 AntdTable 组件。
    参数：
        raw_df (Any): 要转换的输入 pandas DataFrame。
        id (str, 可选): 设置对应 AntdTable 组件的 id，默认为 None。
        columns_alias (dict, 可选): 为指定字段定义充当 title 的别名，默认为 None。
        columns_render_options (dict, 可选): 为指定字段设置对应 AntdTable 原 columns.*.renderOptions 配置参数，默认为 None。
        column_width_mode (Literal['auto', 'fit-title', 'equal'], 可选): 列宽分配策略，可选 'auto'、'fit-title'、'equal'，默认为 'auto'。
        column_width_sum (str, 可选): 用于定义各列宽之和，常用的有 '100%'、'1000px' 等符合 CSS 宽度规则的值，默认为 '100%'。
        left_fixed_columns (List[str], 可选): 定义需要在左侧固定的列名数组，默认为 None。
        right_fixed_columns (List[str], 可选): 定义需要在右侧固定的列名数组，默认为 None。
        numeric_auto_sort (bool, 可选): 是否针对数据框中的数值型字段自动添加排序功能，默认为 True。
        sort_multiple (Union[bool, Literal['auto']], 可选): 针对字段排序配置组合排序相关参数，默认值同 AntdTable 的 sortOptions.multiple，默认为 False。
        str_auto_filter (bool, 可选): 是否针对数据框中的字符型字段自动添加筛选功能，默认为 True。
        str_max_unique_value_count (int, 可选): 设置筛选功能的字符型字段唯一值数量上限，默认为 20。
        checkbox_filter_radio_columns (List[str], 可选): 将筛选功能设置为单选模式的字段名数组，默认为空列表。
        checkbox_filter_enable_search (bool, 可选): 字段筛选菜单是否启用搜索框，默认为 True。
        editable_columns (List[str] | Literal['*'], 可选): 设置需要开启可编辑功能的列名数组，传入 '*' 表示全部字段均开启可编辑功能，默认为 None。
        columns_precision (dict, 可选): 为指定字段设置小数保留位数，当传入 {'*': 小数位数} 时，表示对所有数值型字段统一设置保留位数，默认为 None。
        columns_processor (Dict[str, Callable], 可选): 对指定字段进行预处理的自定义函数，默认为 None。
        **kwargs: 其他传递给 AntdTable 组件的参数。
    返回值：
        fac.AntdTable: 从输入 DataFrame 生成的 AntdTable 组件。
    """

    # 默认参数定义
    columns_alias = columns_alias or {}
    columns_alias = {
        column: columns_alias.get(column) or column
        for column in raw_df.columns
    }
    columns_render_options = columns_render_options or {}
    left_fixed_columns = left_fixed_columns or []
    right_fixed_columns = right_fixed_columns or []
    checkbox_filter_radio_columns = (
        checkbox_filter_radio_columns or []
    )
    editable_columns = editable_columns or []
    columns_precision = columns_precision or {}
    columns_processor = columns_processor or {}

    # 拷贝源数据框，防止修改源数据
    output_df = pd.DataFrame(raw_df).copy(deep=True)

    # 构造必选参数
    # 构造columns参数
    columns = []
    for column in output_df.columns:
        columns.append(
            {
                'dataIndex': column,
                'title': columns_alias.get(column),
            }
        )
    # 根据column_width_mode构造列宽
    if column_width_mode == 'fit-title':
        # 计算所有字段名字符数之和
        columns_title_length_sum = sum(
            output_df.columns.map(
                lambda s: len(columns_alias.get(s))
            )
        )
        # 为各字段按比例分配列宽
        for i, column in enumerate(columns):
            columns[i]['width'] = 'calc({} * {} )'.format(
                column_width_sum,
                len(column['title'])
                / columns_title_length_sum,
            )
    elif column_width_mode == 'equal':
        for i, column in enumerate(columns):
            columns[i]['width'] = 'calc({} / {})'.format(
                column_width_sum, len(columns)
            )
    # 根据left_fixed_columns、right_fixed_columns为相应字段设置是否固定
    for i, column in enumerate(columns):
        if column['dataIndex'] in left_fixed_columns:
            columns[i]['fixed'] = 'left'
        elif column['dataIndex'] in right_fixed_columns:
            columns[i]['fixed'] = 'right'
    # 根据editable_columns对相关列开启可编辑功能
    for i, column in enumerate(columns):
        if (
            column['dataIndex'] in editable_columns
            or editable_columns == '*'
        ):
            columns[i]['editable'] = True
    # 根据columns_render_options为columns各字段补充再渲染相关参数
    if columns_render_options:
        for i, column in enumerate(columns):
            if columns_render_options.get(
                column['dataIndex']
            ):
                columns[i]['renderOptions'] = (
                    columns_render_options.get(
                        column['dataIndex']
                    )
                )

    # 构造可选参数
    optional_params = {}
    # 构造sortOptions参数
    if numeric_auto_sort:
        optional_params['sortOptions'] = {
            'sortDataIndexes': output_df.select_dtypes(
                'number'
            ).columns.tolist(),
            'multiple': sort_multiple,
        }
    # 构造filterOptions参数
    if str_auto_filter:
        filterOptions = {}
        for column in output_df.select_dtypes(
            include='object'
        ):
            # 检查当前字符型字段唯一值数量是否小于等于str_max_unique_value_count
            try:
                if (
                    output_df[column].nunique()
                    <= str_max_unique_value_count
                ):
                    filterOptions[column] = {
                        'filterSearch': checkbox_filter_enable_search
                    }
                    # 检查当前字段是否需要设置为单选模式
                    if (
                        column
                        in checkbox_filter_radio_columns
                    ):
                        filterOptions[column][
                            'filterMultiple'
                        ] = False
                else:
                    filterOptions[column] = {
                        'filterMode': 'keyword'
                    }
            # 忽略计算nunique时出现的异常
            except:
                pass
        # 更新到optional_params中
        optional_params['filterOptions'] = filterOptions

    # 数据预处理
    # 根据columns_precision对指定字段进行小数保留处理
    if len(
        columns_precision
    ) == 1 and columns_precision.get('*'):
        for column in output_df.select_dtypes(
            'number'
        ).columns:
            output_df[column] = output_df[column].round(
                columns_precision.get('*')
            )
    else:
        for key in columns_precision.keys():
            output_df[key] = output_df[key].round(
                columns_precision.get(key)
            )
    # 根据columns_processor对指定字段进行自定义预处理
    if columns_processor:
        for key, processor in columns_processor.items():
            output_df[key] = output_df[key].apply(processor)

    return fac.AntdTable(
        # data以kwargs中的data为准
        data=kwargs.get('data')
        or output_df.to_dict('records'),
        columns=columns,
        **optional_params,
        **kwargs,
    )


if __name__ == '__main__':
    pass
