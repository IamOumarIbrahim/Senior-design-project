//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { CLASS_COLOUR, DAYS } from "./colours.js";

// Trend, two lines with 4 points for each day
export function TrendChart(props) {
  const x0 = 40;
  const x1 = 800;
  const y0 = 12;
  const y1 = 160;
  const n = 28;

  let top = 4;
  for (let i = 0; i < n; i++) {
    if (props.a[i] > top) {
      top = props.a[i];
    }
    if (props.b[i] > top) {
      top = props.b[i];
    }
  }

  const grid = [];
  for (let g = 0; g <= 4; g++) {
    const y = y1 - (y1 - y0) * g / 4;
    grid.push(<line key={"l" + g} x1={x0} x2={x1} y1={y} y2={y} stroke="#eef1f5" />);
    grid.push(
      <text key={"t" + g} x={x0 - 10} y={y + 4} fontSize="11" fill="#8a94a3" textAnchor="end">
        {Math.round(top * g / 4)}
      </text>
    );
  }
  for (let i = 0; i < 7; i++) {
    grid.push(
      <text key={"d" + i} x={x0 + (x1 - x0) * (i * 4 + 2) / n} y="180" fontSize="11" fill="#8a94a3" textAnchor="middle">
        {DAYS[i]}
      </text>
    );
  }

  function line(values, colour, name) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      pts.push([x0 + (x1 - x0) * (i + 0.5) / n, y1 - (y1 - y0) * values[i] / top]);
    }
    let d = "M" + pts[0][0] + "," + pts[0][1];
    for (let i = 1; i < n; i++) {
      const cx = (pts[i - 1][0] + pts[i][0]) / 2;
      d = d + " C" + cx + "," + pts[i - 1][1] + " " + cx + "," + pts[i][1] + " " + pts[i][0] + "," + pts[i][1];
    }
    const area = d + " L" + pts[n - 1][0] + "," + y1 + " L" + pts[0][0] + "," + y1 + " Z";
    const dots = [];
    for (let i = 0; i < n; i++) {
      dots.push(<circle key={name + i} cx={pts[i][0]} cy={pts[i][1]} r="2.6" fill="#fff" stroke={colour} strokeWidth="1.6" />);
    }
    return (
      <g key={name}>
        <path d={area} fill={colour} opacity="0.08" />
        <path d={d} fill="none" stroke={colour} strokeWidth="2.4" />
        {dots}
      </g>
    );
  }

  return (
    <svg width="100%" height="190" viewBox="0 0 820 190">
      {grid}
      {line(props.a, "#2f80ed", "a")}
      {line(props.b, "#f5a524", "b")}
    </svg>
  );
}

// Donut with the legend next to it
export function Donut(props) {
  let total = 0;
  for (let i = 0; i < props.parts.length; i++) {
    total = total + props.parts[i].count;
  }

  const cx = 100;
  const cy = 100;
  const R = 86;
  const r = 62;
  let a0 = -Math.PI / 2;
  const slices = [];
  const legned = [];

  for (let i = 0; i < props.parts.length; i++) {
    const p = props.parts[i];
    // a full circle cant be drawn as one arc
    let a1 = a0 + 2 * Math.PI * p.count / total;
    if (p.count == total) {
      a1 = a0 + 2 * Math.PI * 0.9999;
    }
    let big = 0;
    if (a1 - a0 > Math.PI) {
      big = 1;
    }
    const d = "M" + (cx + R * Math.cos(a0)) + " " + (cy + R * Math.sin(a0))
      + " A" + R + " " + R + " 0 " + big + " 1 " + (cx + R * Math.cos(a1)) + " " + (cy + R * Math.sin(a1))
      + " L" + (cx + r * Math.cos(a1)) + " " + (cy + r * Math.sin(a1))
      + " A" + r + " " + r + " 0 " + big + " 0 " + (cx + r * Math.cos(a0)) + " " + (cy + r * Math.sin(a0)) + " Z";
    slices.push(<path key={p.key} d={d} fill={CLASS_COLOUR[p.key]} stroke="#fff" strokeWidth="2" />);
    a0 = a1;

    const y = 40 + i * 26;
    legned.push(
      <g key={"k" + p.key}>
        <circle cx="222" cy={y - 4} r="5" fill={CLASS_COLOUR[p.key]} />
        <text x="236" y={y} fontSize="13" fill="#3b4656">{p.name}</text>
        <text x="462" y={y} fontSize="13" fill="#3b4656" textAnchor="end">
          {p.count + " (" + Math.round(100 * p.count / total) + "%)"}
        </text>
      </g>
    );
  }

  return (
    <svg width="100%" height="200" viewBox="0 0 470 200">
      {slices}
      <text x={cx} y={cy + 4} fontSize="30" fontWeight="700" textAnchor="middle" fill="#1b2430">{total}</text>
      <text x={cx} y={cy + 26} fontSize="12" textAnchor="middle" fill="#6b7686">Total detections</text>
      {legned}
    </svg>
  );
}

// Heatmap, weekday and hour
export function Heatmap(props) {
  const hx0 = 44;
  const cw = (800 - hx0) / 24;
  const ch = 24;

  let top = 0.01;
  for (let d = 0; d < 7; d++) {
    for (let h = 0; h < 24; h++) {
      if (props.heat[d][h] > top) {
        top = props.heat[d][h];
      }
    }
  }

  function ramp(t) {
    const a = [255, 243, 234];
    const b = [198, 40, 40];
    const c = [];
    for (let i = 0; i < 3; i++) {
      c.push(Math.round(a[i] + (b[i] - a[i]) * t));
    }
    return "rgb(" + c[0] + "," + c[1] + "," + c[2] + ")";
  }

  const cells = [];
  for (let d = 0; d < 7; d++) {
    cells.push(
      <text key={"d" + d} x={hx0 - 8} y={d * ch + ch * 0.7 + 4} fontSize="11" fill="#8a94a3" textAnchor="end">{DAYS[d]}</text>
    );
    for (let h = 0; h < 24; h++) {
      cells.push(
        <rect key={d + "-" + h} x={hx0 + h * cw + 1} y={d * ch + 4} width={cw - 2} height={ch - 3} rx="2.5" fill={ramp(props.heat[d][h] / top)}>
          <title>{DAYS[d] + " " + h + ":00  " + props.heat[d][h] + " alerts per hour"}</title>
        </rect>
      );
    }
  }
  for (let h = 0; h < 24; h = h + 3) {
    let word = h + ":00";
    if (h < 10) {
      word = "0" + word;
    }
    cells.push(
      <text key={"h" + h} x={hx0 + h * cw + cw / 2} y={7 * ch + 20} fontSize="11" fill="#8a94a3" textAnchor="middle">{word}</text>
    );
  }

  return <svg width="100%" height="200" viewBox="0 0 820 200">{cells}</svg>;
}

// Timeline of one trip
export function Timeline(props) {
  const left = 50;
  const width = 750;
  let total = props.minutes;
  if (total <= 0) {
    total = 1;
  }

  const items = [];
  for (let i = 0; i < props.marks.length; i++) {
    const m = props.marks[i];
    items.push(
      <circle key={i} cx={left + width * m.minute / total} cy="24" r="5.5" fill={CLASS_COLOUR[m.class]}>
        <title>{m.class + " at " + m.minute + " min"}</title>
      </circle>
    );
  }

  let step = 15;
  if (total < 30) {
    step = 5;
  }
  if (total < 10) {
    step = 2;
  }
  const labels = [];
  for (let t = 0; t <= total; t = t + step) {
    labels.push(
      <text key={"t" + t} x={left + width * t / total} y="56" fontSize="11" fill="#8a94a3" textAnchor="middle">{t + " min"}</text>
    );
  }

  return (
    <svg width="100%" height="64" viewBox="0 0 820 64">
      <line x1={left} x2={left + width} y1="24" y2="24" stroke="#e3eaf3" strokeWidth="6" strokeLinecap="round" />
      {items}
      {labels}
    </svg>
  );
}
