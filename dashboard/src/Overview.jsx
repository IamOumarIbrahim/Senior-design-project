//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { Donut, Heatmap, Timeline, TrendChart } from "./charts.jsx";
import { CLASS_COLOUR, CLASS_ICON } from "./colours.js";
import Icon from "./Icon.jsx";

function driveText(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.round((seconds - h * 3600) / 60);
  return h + " h " + m + " m";
}

// goes up or down comapred to last week
function changeText(value, upIsBad) {
  if (value == null) {
    return <span>no data for last week</span>;
  }
  let arrow = "↓ ";
  let good = upIsBad;
  if (value > 0) {
    arrow = "↑ ";
    good = upIsBad == false;
  }
  let colour = "#27ae60";
  if (good == false) {
    colour = "#eb5757";
  }
  return <span><b style={{ color: colour }}>{arrow + Math.abs(value) + "%"}</b> vs. last week</span>;
}

function Kpi(props) {
  return (
    <div className="card k">
      <div className="ic" style={{ background: props.bg }}>
        <Icon name={props.icon} size={22} colour={props.colour} />
      </div>
      <div>
        <div className="l">{props.label}</div>
        <div className="v">{props.value}</div>
        <div className="d">{props.note}</div>
      </div>
    </div>
  );
}

function moveWeek(text, days) {
  const d = new Date(text + "T12:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().substring(0, 10);
}

function Overview(props) {
  const data = props.data;
  const kpi = data.kpi;

  let monitored = "-";
  if (kpi.monitored != null) {
    monitored = kpi.monitored + "%";
  }

  const dets = [];
  for (let i = 0; i < data.recent.length; i++) {
    const r = data.recent[i];
    dets.push(
      <div className="det" key={i}>
        <div className="ic" style={{ background: CLASS_COLOUR[r.class] + "22" }}>
          <Icon name={CLASS_ICON[r.class]} size={18} colour={CLASS_COLOUR[r.class]} />
        </div>
        <div className="t">{r.name}<small>{r.message}</small></div>
        <div className="tm">{r.clock}<br />{r.duration + " s"}</div>
      </div>
    );
  }

  const tips = [];
  for (let i = 0; i < data.tips.length && i < 2; i++) {
    tips.push(
      <div className="tip" key={i}>
        <div className="ic" style={{ background: "#fff4e2" }}><Icon name="bulb" size={16} colour="#f5a524" /></div>
        <div>{data.tips[i]}</div>
      </div>
    );
  }

  let sample = null;
  if (data.sample) {
    sample = <span className="sample">SAMPLE DATA</span>;
  }

  return (
    <div className="page">
      <div className="head">
        <div>
          <h1>Driving Overview {sample}</h1>
          <p>Your driving safety at a glance</p>
        </div>
        <div className="date">
          <button onClick={function () { props.setWeek(moveWeek(data.week_start, -7)); }}>‹</button>
          <Icon name="cal" size={18} colour="#4a5565" />
          {data.week_start + " to " + data.week_end}
          <button onClick={function () { props.setWeek(moveWeek(data.week_start, 7)); }}>›</button>
        </div>
      </div>

      <div className="kpis">
        <Kpi icon="wheel" bg="#eef1f5" colour="#1b2430" label="Total Drive Time" value={driveText(kpi.drive_s)} note={changeText(kpi.drive_change, false)} />
        <Kpi icon="warn" bg="#fdecec" colour="#eb5757" label="Distraction Detections" value={kpi.distraction} note={changeText(kpi.distraction_change, true)} />
        <Kpi icon="zzz" bg="#fff4e2" colour="#f5a524" label="Drowsiness Detections" value={kpi.drowsiness} note={changeText(kpi.drowsiness_change, true)} />
        <Kpi icon="shield" bg="#eaf2fe" colour="#2f80ed" label="Drive Time Monitored" value={monitored} note={"camera blocked " + kpi.blocked_min + " min total"} />
      </div>

      <div className="row wide">
        <div className="card">
          <h3>Distraction &amp; Drowsiness Trend
            <span className="lg">
              <span><i style={{ background: "#2f80ed" }}></i>Distraction</span>
              <span><i style={{ background: "#f5a524" }}></i>Drowsiness</span>
            </span>
          </h3>
          <TrendChart a={data.trend_distraction} b={data.trend_drowsiness} />
        </div>
        <div className="card">
          <h3>Detection Breakdown</h3>
          <Donut parts={data.breakdown} />
        </div>
      </div>

      <div className="row wide">
        <div className="stack">
          <div className="card">
            <h3>Driving Activity Heatmap <span className="lg">alerts per hour of driving</span></h3>
            <Heatmap heat={data.heat} />
          </div>
          <div className="card">
            <h3>Last Trip Timeline <span className="lg">{data.last_trip.minutes + " min"}</span></h3>
            <Timeline marks={data.last_trip.marks} minutes={data.last_trip.minutes} />
          </div>
        </div>
        <div className="card">
          <h3>Recent Detections</h3>
          {dets}
          <div className="tips">
            <h3>Post-trip tip</h3>
            {tips}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Overview;
