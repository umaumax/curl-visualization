#!/usr/bin/env python3
import argparse
import json
import statistics
import os

import pandas as pd

import streamlit as st

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

pio.templates.default = "plotly"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Streamlit app for visualizing curl metrics")
    parser.add_argument(
        "--default-json",
        type=str,
        help="Path to the default JSON file to load",
        default=None,
    )
    parser.add_argument(
        "--title",
        type=str,
        help="Title for the data",
        default=None,
    )
    return parser.parse_args()


def load_default_json(file_path):
    if file_path and os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return None


def main():
    args = parse_arguments()

    st.set_page_config(
        page_title="cURL Metrics Visualization",
        initial_sidebar_state="collapsed")

    st.title("cURL Metrics Visualization")

    st.header('Data')

    title = st.text_input(
        'title',
        '',
        placeholder=args.title)
    if not title and args.title:
        title = args.title
    file_name_prefix = title + '-' if title else ''

    def create_download_button(label, data, file_name):
        st.download_button(
            label,
            data,
            file_name=f'{file_name_prefix}{file_name}',
            key=file_name,
        )

    default_data = load_default_json(args.default_json)

    if default_data:
        st.sidebar.success(f"Loaded default JSON: {args.default_json}")
    else:
        st.sidebar.info("No default JSON file loaded.")

    uploaded_file = st.file_uploader("Upload JSON File", type="json")

    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.success("Using uploaded JSON file.")
        except Exception as e:
            st.error(f"Error reading the uploaded JSON file: {e}")
            return
    elif default_data:
        data = default_data
        st.success("Using default JSON file.")
    else:
        st.info(
            "Please upload a JSON file or provide a default JSON file via --default-json.")
        return

    keys = data[0].keys()
    metrics = [
        "time_namelookup",
        "time_connect",
        "time_redirect",
        "time_appconnect",
        "time_pretransfer",
        "time_starttransfer",
        "time_total",
    ]
    if not set(metrics).issubset(set(keys)):
        st.error(
            f'There are no {metrics} fields in the input data. {list(keys)}')
        return False
    if "time_posttransfer" in keys:
        metrics = [
            "time_namelookup",
            "time_connect",
            "time_redirect",
            "time_appconnect",
            "time_pretransfer",
            "time_starttransfer",
            "time_posttransfer",  # added
            "time_total",
        ]
    stats = {}

    for metric in metrics:
        values = [entry[metric] for entry in data]
        stats[metric] = {
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "variance": statistics.variance(values) if len(values) > 1 else 0,
            "stdev": statistics.stdev(values) if len(values) > 1 else 0,
            "values": values,
        }

    st.header(f"Mean, Min, Max{ ' : '+title if title else ''}")
    labels = list(stats.keys())
    means = [stat["mean"] for stat in stats.values()]
    mins = [stat["min"] for stat in stats.values()]
    maxs = [stat["max"] for stat in stats.values()]
    variances = [stat["variance"] for stat in stats.values()]
    stdevs = [stat["stdev"] for stat in stats.values()]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=labels,
            y=means,
            name='Mean',
            marker_color='skyblue'))
    fig.add_trace(
        go.Bar(
            x=labels,
            y=mins,
            name='Min',
            marker_color='lightgreen'))
    fig.add_trace(go.Bar(x=labels, y=maxs, name='Max', marker_color='salmon'))
    # NOTE: Different numerical order of comparison
    # fig.add_trace(
    # go.Bar(
    # x=labels,
    # y=variances,
    # name='Variance',
    # marker_color='purple'))
    fig.add_trace(
        go.Bar(
            x=labels,
            y=stdevs,
            name='Standard Deviation',
            marker_color='orange'))

    fig.update_layout(
        title="Metrics Summary",
        xaxis_title="Metrics",
        yaxis_title="Time (s)",
        barmode='group',
    )
    st.plotly_chart(fig)
    create_download_button(
        "Download",
        pio.to_html(fig),
        file_name='curl-metrics-summary.html'
    )

    with st.expander("details..."):
        st.header(f"Statistics Table{ ' : '+title if title else ''}")
        stats_table = {
            metric: [
                stat["mean"],
                stat["min"],
                stat["max"],
                stat["variance"]] for metric,
            stat in stats.items()}
        stats_df = pd.DataFrame(
            stats_table,
            index=[
                "Mean",
                "Min",
                "Max",
                "Variance"]).T
        st.dataframe(stats_df, use_container_width=True)
        create_download_button(
            "Download",
            stats_df.transpose().to_json(indent=4),
            file_name='curl-statistics.json'
        )

    st.header(f"Requests Times{ ' : '+title if title else ''}")

    fig = go.Figure()
    for metric in labels:
        values = stats[metric]["values"]
        fig.add_trace(
            go.Scatter(
                x=list(
                    range(
                        len(values))),
                y=values,
                mode='lines+markers',
                name=metric))

    fig.update_layout(
        title="Metrics per Request",
        xaxis_title="Request Index",
        yaxis_title="Time (s)",
        legend_title="Metrics"
    )
    fig.update_layout(coloraxis=dict(cmax=6, cmin=3))
    st.plotly_chart(fig)
    create_download_button(
        "Download",
        pio.to_html(fig),
        file_name='curl-metrics-per-request.html'
    )

    def calculate_timeline_with_offset(data):
        timeline = []
        # NOTE: for debug
        # start_offset = min([entry['time_offset'] for entry in data])
        start_offset = 0
        for entry in data:
            # NOTE: If there is no redirect, the value is 0.
            if entry["time_redirect"] == 0:
                entry["time_redirect"] = entry["time_connect"]

            stages = {
                "DNS Lookup(time_namelookup)": entry["time_namelookup"],
                "Connection(time_connect)": entry["time_connect"] - entry["time_namelookup"],
                "Redirected(time_redirect)": entry["time_redirect"] - entry["time_connect"],
                "SSL Handshake(time_appconnect)": entry["time_appconnect"] - entry["time_redirect"],
                "Request Preparation(time_pretransfer)": entry["time_pretransfer"] - entry["time_appconnect"],
                "Time to First Byte Received(time_starttransfer)": entry["time_starttransfer"] - entry["time_pretransfer"],
                "End(time_total)": entry["time_total"] - entry["time_starttransfer"],
            }
            if "time_posttransfer" in entry:
                del stages["End(time_total)"]
                stages["Time to Last Byte Sent(time_posttransfer)"] = \
                    entry["time_posttransfer"] - entry["time_starttransfer"]
                stages["End(time_total)"] = \
                    entry["time_total"] - entry["time_posttransfer"]

            start_time = entry["time_offset"] - start_offset
            adjusted_timeline = []
            for stage, duration in stages.items():
                adjusted_timeline.append((stage, start_time, duration))
                start_time += duration
            timeline.append(adjusted_timeline)
        return timeline

    def plot_timeline_with_offset(timeline):
        df_list = []
        for idx, sublist in enumerate(timeline):
            df = pd.DataFrame(sublist, columns=['stage', 'start', 'duration'])
            df['group'] = idx
            df_list.append(df)
        df = pd.concat(df_list, ignore_index=True)
        df['end'] = df['start'] + df['duration']
        df['start'] = pd.to_datetime(
            df['start'], unit='s', utc=True) .dt.tz_convert('Asia/Tokyo')
        df['end'] = pd.to_datetime(
            df['end'], unit='s', utc=True).dt.tz_convert('Asia/Tokyo')
        fig = px.timeline(
            df,
            x_start="start",
            x_end="end",
            y="group",
            color="stage",
            hover_data={
                # NOTE: This filed is also shown as a hover text.
                "duration": True,
            },
            title="Task Timeline"
        )

        return fig

    if "time_offset" in data[0].keys():
        st.header(f"Timeline{ ' : '+title if title else ''}")
        timeline = calculate_timeline_with_offset(data)
        fig = plot_timeline_with_offset(timeline)
        st.plotly_chart(fig)
        create_download_button(
            "Download",
            pio.to_html(fig),
            file_name='curl-timeline.html'
        )

    st.markdown('''
    ## link
    [curl - time_ prefix fields document]( https://curl.se/docs/manpage.html#timeappconnect )
    ''')


if __name__ == "__main__":
    main()
