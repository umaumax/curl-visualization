#!/usr/bin/env python3
import argparse
import json
import statistics
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
import pandas as pd
import os


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

    x = np.arange(len(labels))
    width = 0.2

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, means, width, label='Mean', color='skyblue')
    ax.bar(x, mins, width, label='Min', color='lightgreen')
    ax.bar(x + width, maxs, width, label='Max', color='salmon')
    ax.set_xlabel('Metrics')
    ax.set_ylabel('Time (s)')
    ax.set_title('Metrics Summary')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.legend()
    st.pyplot(fig)

    st.header("Line Chart: Per Request Values")

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    for i, metric in enumerate(labels):
        values = stats[metric]["values"]
        ax2.plot(range(len(values)), values, marker='o', label=metric)

    ax2.set_xlabel('Request Index')
    ax2.set_ylabel('Time (s)')
    ax2.set_title('Metrics per Request')
    ax2.legend()
    ax2.grid()
    st.pyplot(fig2)

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
        num_requests = len(timeline)
        stages = [stage[0] for stage in timeline[0]]
        colors = [
            "#FF9999",
            "#66B2FF",
            "#99FF99",
            "#FFD700",
            "#FFB266",
            "#66FFFF"]

        fig, ax = plt.subplots(figsize=(12, 6))
        bar_height = 0.4

        for i, request in enumerate(timeline):
            for j, (stage, start_time, duration) in enumerate(request):
                ax.barh(
                    i,
                    duration,
                    left=start_time,
                    height=bar_height,
                    color=colors[j],
                    label=stage if i == 0 else "")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Request Index")
        ax.set_title("Curl Metrics Timeline with Time Offset")
        y_step = 10
        ax.set_yticks(range(0, num_requests, y_step))
        ax.set_yticklabels(
            [f"[{i}]" for i in range(0, num_requests, y_step)])
        ax.legend(loc="lower right")
        ax.grid(axis="x", linestyle="--", alpha=0.7)

        return fig

    if "time_offset" in data[0].keys():
        timeline = calculate_timeline_with_offset(data)
        fig = plot_timeline_with_offset(timeline)
        st.pyplot(fig)


if __name__ == "__main__":
    main()
