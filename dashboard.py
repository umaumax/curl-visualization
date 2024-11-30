#!/usr/bin/env python3
import argparse
import json
import statistics
import streamlit as st
import numpy as np
import pandas as pd
import os
import plotly.graph_objects as go


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Streamlit app for visualizing curl metrics")
    parser.add_argument(
        "--default-json",
        type=str,
        help="Path to the default JSON file to load",
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
        page_title="Curl Metrics Visualization",
        initial_sidebar_state="collapsed")

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

    metrics = data[0].keys()
    metrics = [key for key in metrics if key != "time_offset"]
    stats = {}

    for metric in metrics:
        values = [entry[metric] for entry in data]
        stats[metric] = {
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "variance": statistics.variance(values) if len(values) > 1 else 0,
            "values": values,
        }

    st.header("Statistics Table")
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

    st.header("Bar Chart: Mean, Min, Max")

    labels = list(stats.keys())
    means = [stat["mean"] for stat in stats.values()]
    mins = [stat["min"] for stat in stats.values()]
    maxs = [stat["max"] for stat in stats.values()]

    fig = go.Figure()

    fig.add_trace(go.Bar(x=labels, y=means, name='Mean', marker_color='skyblue'))
    fig.add_trace(go.Bar(x=labels, y=mins, name='Min', marker_color='lightgreen'))
    fig.add_trace(go.Bar(x=labels, y=maxs, name='Max', marker_color='salmon'))

    fig.update_layout(
        title="Metrics Summary",
        xaxis_title="Metrics",
        yaxis_title="Time (s)",
        barmode='group',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig)

    st.header("Line Chart: Per Request Values")

    fig2 = go.Figure()

    for metric in labels:
        values = stats[metric]["values"]
        fig2.add_trace(go.Scatter(x=list(range(len(values))), y=values, mode='lines+markers', name=metric))

    fig2.update_layout(
        title="Metrics per Request",
        xaxis_title="Request Index",
        yaxis_title="Time (s)",
        legend_title="Metrics"
    )
    st.plotly_chart(fig2)

    def calculate_timeline_with_offset(data):
        timeline = []
        start_offset = min([entry['time_offset'] for entry in data])
        for entry in data:
            stages = {
                "DNS Lookup": entry["time_namelookup"],
                "Connection": entry["time_connect"] - entry["time_namelookup"],
                "SSL Handshake": entry["time_appconnect"] - entry["time_connect"],
                "Request Preparation": entry["time_pretransfer"] - entry["time_appconnect"],
                "Time to First Byte": entry["time_starttransfer"] - entry["time_pretransfer"],
                "Total": entry["time_total"] - entry["time_starttransfer"],
            }

            start_time = entry["time_offset"] - start_offset
            adjusted_timeline = []
            for stage, duration in stages.items():
                adjusted_timeline.append((stage, start_time, duration))
                start_time += duration
            timeline.append(adjusted_timeline)
        return timeline

    def plot_timeline_with_offset(timeline):
        colors = [
            "#FF9999",
            "#66B2FF",
            "#99FF99",
            "#FFD700",
            "#FFB266",
            "#66FFFF"]
        
        fig = go.Figure()

        for i, request in enumerate(timeline):
            start_time = 0
            for j, (stage, start, duration) in enumerate(request):
                fig.add_trace(go.Bar(
                    x=[stage],
                    y=[duration],
                    base=start_time,
                    name=stage,
                    marker_color=colors[j],
                    hoverinfo="x+y"
                ))
                start_time += duration

        fig.update_layout(
            title="Curl Metrics Timeline with Time Offset",
            xaxis_title="Time (s)",
            yaxis_title="Request Index",
            barmode="stack",
            xaxis=dict(tickmode="linear"),
            showlegend=True
        )

        return fig

    if "time_offset" in data[0].keys():
        timeline = calculate_timeline_with_offset(data)
        fig = plot_timeline_with_offset(timeline)
        st.plotly_chart(fig)


if __name__ == "__main__":
    main()
