//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { CLASS_COLOUR } from "./colours.js";

function Statistics(props) {
  const parts = props.data.breakdown;

  let top = 1;
  for (let i = 0; i < parts.length; i++) {
    if (parts[i].count > top) {
      top = parts[i].count;
    }
  }

  const bars = [];
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    bars.push(
      <div className="bar" key={p.key}>
        <div className="name">{p.name}</div>
        <div className="track">
          <i style={{ width: (100 * p.count / top) + "%", background: CLASS_COLOUR[p.key] }}></i>
        </div>
        <div className="num">{p.count}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="head">
        <div>
          <h1>Statistics</h1>
          <p>{props.data.week_start + " to " + props.data.week_end}</p>
        </div>
      </div>
      <div className="card">
        <h3>Detections by class</h3>
        {bars}
      </div>
    </div>
  );
}

export default Statistics;
