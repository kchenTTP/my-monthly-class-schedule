# cspell: ignore dataframe, gsheets, streamlit, Kang's, NYPL, SNFL, selectbox
import streamlit as st
from streamlit_gsheets import GSheetsConnection

from streamlit_calendar import calendar
from datetime import datetime, date, timedelta

import warnings

import numpy as np
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


def process_dataframe(
    df: pd.DataFrame, year: str, include_series_based: bool = False
) -> pd.DataFrame:
    processed_df = df[df["date"].notnull()]
    processed_df = processed_df.loc[
        processed_df["cancelled"] == 0
    ]  # don't show cancelled classes and series based classes
    if not include_series_based:
        processed_df = processed_df.loc[processed_df["series"] == 0]
    processed_df = processed_df[
        [
            "date",
            "day",
            "st time",
            "end time",
            "class",
            "location",
            "lang",
            "drupal link",
        ]
    ]

    # Fix incorrect datatypes
    processed_df["st time"] = (
        year
        + "/"
        + processed_df["date"].astype(str)
        + " "
        + processed_df["st time"].astype(str)
    )
    processed_df["end time"] = (
        year
        + "/"
        + processed_df["date"].astype(str)
        + " "
        + processed_df["end time"].astype(str)
    )
    processed_df["date"] = processed_df["st time"]

    processed_df["date"] = pd.to_datetime(processed_df["date"], errors="coerce")
    processed_df["st time"] = pd.to_datetime(processed_df["st time"], errors="coerce")
    processed_df["end time"] = pd.to_datetime(processed_df["end time"], errors="coerce")
    processed_df["day"] = processed_df["date"].dt.day_name()

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


def process_drupal_link(df: pd.DataFrame) -> pd.DataFrame:
    df.loc[df["st time"] < datetime.now(), "drupal link"] = np.nan

    return processed_df


def get_calender_event_list(df: pd.DataFrame) -> list[dict]:
    event_list = []
    for _, row in df.iterrows():
        event_dict = {
            "title": row["class"],
            "color": st.session_state.LOCATION_COLOR_MAP.get(row["location"]),
            "start": row["st time"].strftime("%Y-%m-%dT%H:%M:%S"),
            "end": row["end time"].strftime("%Y-%m-%dT%H:%M:%S"),
            "resourceId": st.session_state.LOCATION_RESOURCE_ID_MAP.get(
                row["location"]
            ),
        }
        event_list.append(event_dict)

    return event_list


def get_first_day_of_month(month_str: str) -> str:
    year, month_name = month_str.split()
    month_number = datetime.strptime(month_name, "%B").month

    return f"{year}-{month_number:02d}-01"


# STREAMLIT
st.set_page_config(
    page_title="Kang's NYPL Teaching Schedule",
    initial_sidebar_state="expanded",
    layout="wide",
)


# Ignore panda warnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

if "LOCATIONS_LIST" not in st.session_state:
    st.session_state["LOCATIONS_LIST"] = ["Chatham Sq", "Online", "Seward Park", "SNFL"]
if "LOCATION_RESOURCE_ID_MAP" not in st.session_state:
    st.session_state["LOCATION_RESOURCE_ID_MAP"] = {
        "Chatham Sq": "chatham",
        "Online": "online",
        "Seward Park": "seward",
        "SNFL": "snfl",
    }
if "LANGUAGES_DICT" not in st.session_state:
    st.session_state["LANGUAGES_DICT"] = {"en": "English", "zh": "Chinese"}
if "LOCATION_COLOR_MAP" not in st.session_state:
    st.session_state["LOCATION_COLOR_MAP"] = {
        "Chatham Sq": "#54BCD6",
        "Online": "#D65654",
        "Seward Park": "#D6C853",
        "SNFL": "#8F62BF",
    }


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

        st.subheader("Series Based Classes")
        series_based_class = st.toggle("Include Series Based Classes", value=False)

    st.markdown(
        """
                *For more technology classes offered by The New York Public Library visit: __[here](https://nypl.org/computers)__*
                """
    )


st.title("Kang's NYPL Monthly Class Schedule")
st.divider()

if selected_month is not None:
    year, month = selected_month.split()

    df = get_sheet_for_month(selected_month)
    processed_df = process_dataframe(
        df, year=year, include_series_based=series_based_class
    )
    # remove link if current time is greater that start time
    processed_df = process_drupal_link(processed_df)

    # TODO: Try Catch when location or language list is empty
    processed_df = get_location_df(processed_df, locations=selected_locations)
    processed_df = get_language_df(processed_df, languages=selected_languages)
    print(processed_df.info())

    # st.markdown(f"### {selected_month}")

    st.code(
        """
        Note: Chatham Square and Seward Park classes operate on a convenient walk-in basis
        Registration is not required, and participants are admitted on a first-come, first-served basis
        """,
        language="java",
    )

    # Table View
    st.dataframe(
        processed_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "date": st.column_config.DateColumn("Date", format="YYYY/MM/DD"),
            "day": st.column_config.TextColumn("Day"),
            "st time": st.column_config.TimeColumn("Start Time", format="hh:mm a"),
            "end time": st.column_config.TimeColumn("End Time", format="hh:mm a"),
            "class": st.column_config.TextColumn("Class Title"),
            "location": st.column_config.TextColumn("Location", width="small"),
            "lang": st.column_config.TextColumn("Language"),
            "drupal link": st.column_config.LinkColumn(
                "Registration Link", display_text="Register Here", width="small"
            ),
        },
    )
    st.divider()

    # Calender View
    calendar_init_date = get_first_day_of_month(selected_month)

    calendar_resources = [
        {
            "id": st.session_state.LOCATION_RESOURCE_ID_MAP.get("Chatham Sq"),
            "location": "Chatham Square",
        },
        {
            "id": st.session_state.LOCATION_RESOURCE_ID_MAP.get("Online"),
            "location": "Online",
        },
        {
            "id": st.session_state.LOCATION_RESOURCE_ID_MAP.get("Seward Park"),
            "location": "Seward Park",
        },
        {
            "id": st.session_state.LOCATION_RESOURCE_ID_MAP.get("SNFL"),
            "location": "SNFL",
        },
    ]

    calendar_options = {
        "headerToolbar": {
            "left": "title",
            "right": "prev,next timeGridDay,timeGridWeek,dayGridMonth",
        },
        "editable": "false",
        "resources": calendar_resources,
        "selectable": "true",
        "initialView": "dayGridMonth",
        "initialDate": calendar_init_date,
    }

    custom_css = """
        .fc-button {
            border: none
        }
        .fc-scrollgrid {
            border-radius: 8px;
            overflow: hidden;
        }
        .fc-event-past {
            opacity: 0.6;
        }
        .fc-event-time {
            font-style: italic;
        }
        .fc .fc-button-primary:not(:disabled).fc-button-active, .fc .fc-button-primary:not(:disabled):active {
            background-color: #99466C;
            border-color: #99466C;
        }
        .fc .fc-button-group > .fc-button.fc-button-active, .fc .fc-button-group > .fc-button:active, .fc .fc-button-group > .fc-button:focus, .fc .fc-button-group > .fc-button:hover {
            background-color: #99466C;
            border-color: #99466C;
        }
    """

    calendar_events = get_calender_event_list(processed_df)
    calendar = calendar(
        events=calendar_events, options=calendar_options, custom_css=custom_css
    )
