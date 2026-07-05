import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fetch import get_stock_data

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def plot_chart(ticker="AAPL", period="6mo"):
    df = get_stock_data(ticker, period)
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = compute_rsi(df['Close'])

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.2, 0.2],
                        vertical_spacing=0.03,
                        subplot_titles=("Price", "RSI", "Volume"))

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name="Price"
    ), row=1, col=1)

    # SMAs
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['SMA20'],
        line=dict(color='orange', width=1.5), name="SMA 20"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['SMA50'],
        line=dict(color='cyan', width=1.5), name="SMA 50"
    ), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['RSI'],
        line=dict(color='purple', width=1.5), name="RSI"
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Volume
    colors = ['green' if c >= o else 'red'
              for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df['Date'], y=df['Volume'],
        marker_color=colors, name="Volume"
    ), row=3, col=1)

    fig.update_layout(
        title=f"{ticker} - Dashboard",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=800
    )

    return fig