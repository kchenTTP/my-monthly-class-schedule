# cspell: ignore dataframe, gsheets, streamlit, Kang's, NYPL, SNFL, selectbox
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from streamlit_calendar import calendar
from datetime import date, timedelta

import warnings

import pandas as pd


# Functions
def get_months_list() -> list[str]:
    today = date.today()
    first_month = date(2023, 5, 1)

    month = today + timedelta(days=31)  # Start with next month
    months_list = []

    while month >= first_month:
        months_list.append(month.strftime("%Y %B"))
        month -= timedelta(days=31)  # Go back one month

    return months_list


def get_sheet_for_month(month: str) -> pd.DataFrame:
    return conn.read(
        worksheet=month,
        ttl=600,
    )


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    processed_df = df[df["date"].notnull()]
    processed_df = processed_df.loc[
        (processed_df["cancelled"] == 0) & (processed_df["series"] == 0)
    ]  # don't show cancelled classes and series based classes
    processed_df = processed_df[
        ["date", "day", "st time", "end time", "location", "lang", "class"]
    ]

    # TODO: Convert columns to the correct datatype
    #      Column    Non-Null Count  Dtype
    # ---  ------    --------------  -----
    #  0   date      33 non-null     object
    #  1   day       33 non-null     object
    #  2   st time   33 non-null     object
    #  3   end time  33 non-null     object
    #  4   location  33 non-null     object
    #  5   lang      33 non-null     object
    #  6   class     33 non-null     object

    return processed_df


def get_location_df(df: pd.DataFrame, locations: list[str]) -> pd.DataFrame:
    filtered_df = pd.DataFrame()

    for location in locations:
        filtered_df = pd.concat(
            [filtered_df, df[df["location"] == location]], ignore_index=True
        )
    filtered_df = filtered_df.sort_values(by="date", ascending=True)

    return filtered_df


def get_language_df(df: pd.DataFrame, languages: list[str]) -> pd.DataFrame:
    language_keys = list(st.session_state.LANGUAGES_DICT.keys())
    language_values = list(st.session_state.LANGUAGES_DICT.values())

    filtered_df = pd.DataFrame()

    for language in languages:
        idx = language_values.index(language)
        filtered_df = pd.concat(
            [filtered_df, df[df["lang"] == language_keys[idx]]], ignore_index=True
        )
    filtered_df = filtered_df.sort_values(by="date", ascending=True)

    return filtered_df


def get_calender_event_list(df: pd.DataFrame) -> list[dict]:
    # Dict format
    # {
    #     "title": "Event 1",
    #     "start": "2023-07-31T08:30:00",
    #     "end": "2023-07-31T10:30:00",
    #     "resourceId": "a",
    # }
    event_list = []

    for _, row in df.iterrows():
        # TODO: Process start and end time
        event_dict = {
            "title": row["class"],
            "start": row["st time"],
            "end": row["end time"],
            "resourceId": row["location"],
        }
        event_list.append(event_dict)

    return event_list


# STREAMLIT
st.set_page_config(
    page_title="Kang's NYPL Teaching Schedule",
    initial_sidebar_state="expanded",
)


# Ignore panda warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if "LOCATIONS_LIST" not in st.session_state:
    st.session_state["LOCATIONS_LIST"] = ["Chatham Sq", "Online", "Seward Park", "SNFL"]
if "LANGUAGES_DICT" not in st.session_state:
    st.session_state["LANGUAGES_DICT"] = {"en": "English", "zh": "Chinese"}

with st.sidebar:
    st.header("Options")
    with st.container(border=True):
        st.subheader("Month")
        selected_month = st.selectbox("Select a month", options=get_months_list())

        st.subheader("Locations")
        selected_locations = st.multiselect(
            "Choose the location you want to see",
            options=st.session_state.LOCATIONS_LIST,
            default=st.session_state.LOCATIONS_LIST,
        )

        st.subheader("Languages")
        selected_languages = st.multiselect(
            "Choose the languages you want to see",
            options=st.session_state.LANGUAGES_DICT.values(),
            default=st.session_state.LANGUAGES_DICT.values(),
        )


st.title(":rainbow[Kang's NYPL Teaching Schedule]")

if selected_month is not None:
    year = int(selected_month[:4])
    month = selected_month[5:]

    df = get_sheet_for_month(selected_month)
    processed_df = process_dataframe(df)

    # TODO: Try Catch when location or language list is empty
    processed_df = get_location_df(processed_df, locations=selected_locations)
    processed_df = get_language_df(processed_df, languages=selected_languages)

    st.dataframe(
        processed_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="MM/DD"),
            "day": st.column_config.TextColumn("Day"),
            "st time": st.column_config.TextColumn("Start Time"),
            "end time": st.column_config.TextColumn("End Time"),
            "location": st.column_config.TextColumn("Location", width="small"),
            "lang": st.column_config.TextColumn("Language", width="small"),
            "class": st.column_config.TextColumn("Class Title"),
        },
    )

    st.write(processed_df.info())
    st.write(year)
    st.write(month)

    # TODO: Create Calender
    calendar_options = ...
    # calendar_events = get_calender_event_list(processed_df)
    # st.write(calendar_events)
    custom_css = ...

    # calendar = calendar(
    #     events=calendar_events, options=calendar_options, custom_css=custom_css
    # )
    # st.write(calendar)
