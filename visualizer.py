import pymongo
import pandas as pd
import plotly.graph_objects as go
import time


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["MobileGameComments"]


collections = {
    "多平台融合": db["Result"],
    "仅限B站": db["BilibiliResult"],
    "仅限微博": db["WeiboResult"]
}

data_frames = {}
for key, collection in collections.items():
    data = list(collection.find())
    df = pd.DataFrame(data)
    df["month"] = df["time"].apply(lambda x: time.strftime("%Y-%m", time.localtime(x)))
    data_frames[key] = df

all_games = set()
for df in data_frames.values():
    all_games.update(df["game"].unique())
all_games = sorted(list(all_games))

fig = go.Figure()

data_options = ["多平台融合", "仅限B站", "仅限微博"]

for platform_idx, platform in enumerate(data_options):
    df = data_frames[platform]
    for game in all_games:
        game_data = df[df["game"] == game]
        visible = True if platform_idx == 0 else False  
        trace = go.Scatter(
            x=game_data["month"],
            y=game_data["emotion"],
            name=game,
            legendgroup=game,
            showlegend=True,
            visible=visible,
            meta=platform  
        )
        fig.add_trace(trace)

buttons = []
for platform_idx, platform in enumerate(data_options):
    visibility = []
    for trace in fig.data:
        if trace.meta == platform:
            visibility.append(True)
        else:
            visibility.append(False)
    button = dict(
        label=platform,
        method="update",
        args=[{"visible": visibility},
              {"title": f"{platform} 每个游戏每月的情感得分"}]
    )
    buttons.append(button)

fig.update_layout(
    updatemenus=[
        dict(
            type="dropdown",
            direction="down",
            buttons=buttons,
            active=0,
            showactive=True,
            x=1.0,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )
    ],
    xaxis_title="月份",
    yaxis_title="情感得分",
    title="每个游戏每月的情感得分",
    xaxis=dict(rangeslider=dict(visible=True)),
    legend_title="游戏名称"
)


fig.update_layout(
    legend=dict(
        title="游戏名称",
        traceorder="normal"
    )
)


fig.show()