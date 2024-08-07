from components.select_columns import select_columns
from components.select_dataframes import select_dataframes
from components.uploader import convert_df, uploader
from utils import filter_word_in_content, replace_datetime
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="XLSX para CSV",
    page_icon="✍️",
    layout='wide',
)


st.markdown(
    body='''
# Conversor **:violet[(XLSX para CSV)]**
'''
)


uploader()
select_dataframes()
select_columns()
has_columns = all([bool(len(v))
                  for k, v in st.session_state.items() if 'columns_' in k])
has_intersection = 'intersection' in st.session_state

if has_columns and has_intersection:
    dataframes: list[pd.DataFrame] = st.session_state.dataframes
    columns: dict[str, list[str]] = {k.replace(
        'columns_', ''): v for k, v in st.session_state.items() if 'columns_' in k}
    intersection: str = st.session_state.intersection

    df = None
    for dataframe in dataframes:
        if df is None:
            df = dataframe
            continue
        df = pd.merge(df, dataframe, on=intersection)

    for col in df.columns:
        if col.endswith('_x') or col.endswith('_y'):
            base_col = col[:-2]  # Remove o sufixo '_x' ou '_y'
            if base_col in df.columns:
                df[base_col] = df[base_col].combine_first(df[col])
                df.drop(columns=[col], inplace=True)
            else:
                df.rename(columns={col: base_col}, inplace=True)

    cols = set(col for cols in columns.values() for col in cols)
    inter_df: pd.DataFrame = df[[intersection, *cols]].copy()

    for col in inter_df.select_dtypes(include=['object']):
        inter_df[col] = inter_df[col].apply(replace_datetime)

    search = st.text_input(
        label='Pesquise aqui',
        placeholder="Separe com dois espaços caso queria mais de uma busca!",
    )

    inter_df = inter_df.dropna(subset=[intersection])
    inter_df = inter_df[inter_df[intersection].astype(str).str.strip() != '']

    final_df = inter_df.copy()
    if search:
        splitted_search = search.split("  ")

        conditions = [filter_word_in_content(word, inter_df, case=False) for word in splitted_search]

        combined_condition = conditions[0]
        for cond in conditions[1:]:
            combined_condition &= cond

        final_df = inter_df[combined_condition]

    col1, col2 = st.columns(2)

    with col1:
        replace = st.text_input(
            label="Substituir",
            placeholder='Separe com dois espaços caso queria mais de uma correspondência!',
        )
    with col2:
        to = st.text_input(
            label="Para",
            placeholder='Separe com dois espaços caso queria mais de uma correspondência!',
        )

    if replace and to:
        splitted_replace = replace.split("  ")
        splitted_to = to.split("  ")

        if len(splitted_replace) == len(splitted_to):

            for r, t in zip(splitted_replace, splitted_to):

                if filter_word_in_content(r, final_df).any():
                    final_df = final_df.replace(
                        to_replace=r, value=t, regex=True)

    final_df = final_df[[intersection, *(col for sheet in st.session_state.get(
        'sheets') for col in st.session_state[f'columns_{sheet}'])]]

    event = st.dataframe(
        data=final_df,
        hide_index=True,
        use_container_width=True,
        selection_mode='multi-row',
        on_select='rerun',
    )

    if len(event.selection.rows) > 0:
        download_df: pd.DataFrame = final_df.iloc[event.selection.rows]

        csv = convert_df(download_df)
        is_downloaded = st.download_button(
            label="Baixar CSV",
            data=csv,
            file_name="csv-file.csv",
            mime="text/csv",
            use_container_width=True,
        )

        if is_downloaded:
            # st.balloons()
            st.session_state.clear()
            st.rerun()
