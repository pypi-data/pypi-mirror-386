import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly_resampler import FigureResampler

if "flead" not in st.session_state:
    st.write(":red[Please Select Data!]")
    st.stop()

# Load data
fdata = st.session_state.flead.fleader
vdata = st.session_state.vlead.vleader
velocity = st.session_state.velocity
echo = st.session_state.echo
correlation = st.session_state.correlation
pgood = st.session_state.pgood

x = np.arange(0, st.session_state.head.ensembles, 1)
y = np.arange(0, fdata["Cells"][0], 1)

X, Y = np.meshgrid(x, y)


@st.cache_data
def fillplot_matplotlib(data):
    fig, ax = plt.subplots()
    cs = ax.contourf(X, Y, data)
    fig.colorbar(cs)
    st.pyplot(fig)


@st.cache_data
def fillplot_plotly(data, colorscale="balance", title="Data", xaxis="time"):
    if xaxis == "time":
        xdata = st.session_state.date
    elif xaxis == "ensemble":
        xdata = x
    else:
        xdata = x
    fig = FigureResampler(go.Figure())
    data1 = np.where(data == -32768, np.nan, data)
    fig.add_trace(
        go.Heatmap(
            z=data1[:, 0:-1],
            x=xdata,
            y=y,
            colorscale=colorscale,
            hoverongaps=False,
        )
    )
    fig.update_layout(
        xaxis=dict(showline=True, mirror=True),
        yaxis=dict(showline=True, mirror=True),
        title_text=title,
    )
    st.plotly_chart(fig)


@st.cache_data
def lineplot(data, title, xaxis="time"):
    data1 = np.where(data == -32768, np.nan, data)
    if xaxis == "time":
        df = pd.DataFrame({"date": st.session_state.date, title: data1})
        fig = px.line(df, x="date", y=title)
    else:
        df = pd.DataFrame({"ensemble": x, title: data1})
        fig = px.line(df, x="ensemble", y=title)

    st.plotly_chart(fig)


# Introduction
st.header("View Raw Data", divider="orange")
st.write(
    """
Displays all variables available in the raw file. No processing has been carried out. 
Data might be missing because of the quality-check criteria used before deployment.\n 
Either `time` or `ensemble` axis can be chosen as the abscissa (x-axis).
The ordinate (y-axis) for the heatmap is `bins` as the depth correction is not applied. 
"""
)
xbutton = st.radio("Select an x-axis to plot", ["time", "ensemble"], horizontal=True)


tab1, tab2, tab3, tab4 = st.tabs(
    ["Primary Data", "Variable Leader", "Fixed Leader", "Advanced"]
)

with tab3:
    # Fixed Leader Plots
    st.header("Fixed Leader", divider="blue")
    fbutton = st.radio(
        "Select a dynamic variable to plot:", fdata.keys(), horizontal=True
    )
    lineplot(fdata[fbutton], fbutton, xaxis=str(xbutton))

with tab2:
    # Variable Leader Plots
    st.header("Variable Leader", divider="blue")
    vbutton = st.radio(
        "Select a dynamic variable to plot:", vdata.keys(), horizontal=True
    )
    lineplot(vdata[vbutton], vbutton, xaxis=str(xbutton))

with tab1:
    st.header("Velocity, Echo Intensity, Correlation & Percent Good", divider="blue")

    def call_plot(varname, beam, xaxis="time"):
        if varname == "Velocity":
            fillplot_plotly(velocity[beam - 1, :, :], title=varname, xaxis=xaxis)
        elif varname == "Echo":
            fillplot_plotly(echo[beam - 1, :, :], title=varname, xaxis=xaxis)
        elif varname == "Correlation":
            fillplot_plotly(correlation[beam - 1, :, :], title=varname, xaxis=xaxis)
        elif varname == "Percent Good":
            fillplot_plotly(pgood[beam - 1, :, :], title=varname, xaxis=xaxis)

    var_option = st.selectbox(
        "Select a data type", ("Velocity", "Echo", "Correlation", "Percent Good")
    )
    beam = st.radio("Select beam", (1, 2, 3, 4), horizontal=True)
    call_plot(var_option, beam, xaxis=str(xbutton))


with tab4:
    st.header("Advanced Data", divider="blue")
    adv_option = st.selectbox(
        "Select a data type",
        (
            "Bit Result",
            "ADC Channel",
            "Error Status Word 1",
            "Error Status Word 2",
            "Error Status Word 3",
            "Error Status Word 4",
        ),
    )
    if adv_option == "Bit Result":
        bitdata = st.session_state.ds.variableleader.bitresult()
        st.subheader("BIT Result", divider="orange")
        st.write("""
        This field contains the results of Workhorse ADCPs builtin test functions.
        A zero indicates a successful BIT result.
        """)
        bitbutton = st.radio(
            "Select a dynamic variable to plot:", bitdata.keys(), horizontal=True
        )
        lineplot(bitdata[bitbutton], bitbutton, xaxis=str(xbutton))

    elif adv_option == "ADC Channel":
        adcdata = st.session_state.vlead.adc_channel()
        st.subheader("ADC Channel", divider="orange")
        adcbutton = st.radio(
            "Select a dynamic variable to plot:", adcdata.keys(), horizontal=True
        )
        lineplot(adcdata[adcbutton], adcbutton, xaxis=str(xbutton))
    elif adv_option == "Error Status Word 1":
        errordata1 = st.session_state.vlead.error_status_word(esw=1)
        st.subheader("Error Status Word", divider="orange")
        errorbutton = st.radio(
            "Select a dynamic variable to plot:", errordata1.keys(), horizontal=True
        )
        lineplot(errordata1[errorbutton], errorbutton, xaxis=str(xbutton))
    elif adv_option == "Error Status Word 2":
        errordata2 = st.session_state.vlead.error_status_word(esw=2)
        errorbutton = st.radio(
            "Select a dynamic variable to plot:", errordata2.keys(), horizontal=True
        )
        lineplot(errordata2[errorbutton], errorbutton, xaxis=str(xbutton))
    elif adv_option == "Error Status Word 3":
        errordata3 = st.session_state.vlead.error_status_word(esw=3)
        errorbutton = st.radio(
            "Select a dynamic variable to plot:", errordata3.keys(), horizontal=True
        )
        lineplot(errordata3[errorbutton], errorbutton, xaxis=str(xbutton))
    elif adv_option == "Error Status Word 4":
        errordata4 = st.session_state.vlead.error_status_word(esw=4)
        errorbutton = st.radio(
            "Select a dynamic variable to plot:", errordata4.keys(), horizontal=True
        )
        lineplot(errordata4[errorbutton], errorbutton, xaxis=str(xbutton))
