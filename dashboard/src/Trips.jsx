//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { useEffect, useState } from "react";
import { getData } from "./api.js";
import { Timeline } from "./charts.jsx";

function Trips(props) {
  const [trips, setTrips] = useState(null);
  const [open, setOpen] = useState(null);

  useEffect(function () {
    getData("/api/v1/trips", props.token, props.onLogout).then(function (d) {
      setTrips(d);
    });
  }, []);

  function show(id) {
    getData("/api/v1/trips/" + id, props.token, props.onLogout).then(function (d) {
      setOpen(d);
    });
  }

  if (trips == null) {
    return <div className="card">Loading ...</div>;
  }

  const lines = [];
  for (let i = 0; i < trips.length; i++) {
    const t = trips[i];
    let monitored = "-";
    if (t.monitored != null) {
      monitored = t.monitored + "%";
    }
    lines.push(
      <tr key={t.session_id} onClick={function () { show(t.session_id); }}>
        <td>{t.started_at.replace("T", " ").substring(0, 16)}</td>
        <td>{t.minutes + " min"}</td>
        <td>{t.events}</td>
        <td>{monitored}</td>
      </tr>
    );
  }

  let detail = null;
  if (open != null) {
    const rows = [];
    for (let i = 0; i < open.events.length; i++) {
      const e = open.events[i];
      rows.push(
        <tr key={i}>
          <td>{e.clock}</td>
          <td>{e.name}</td>
          <td>{"Tier " + e.tier}</td>
          <td>{e.message}</td>
        </tr>
      );
    }
    detail = (
      <div className="card">
        <h3>{"Trip of " + open.started_at.replace("T", " ").substring(0, 16)}</h3>
        <Timeline marks={open.marks} minutes={open.minutes} />
        <table><tbody>{rows}</tbody></table>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="head"><div><h1>Trips</h1><p>Click a trip to see what happened</p></div></div>
      <div className="card">
        <table className="click">
          <thead><tr><th>Started</th><th>Length</th><th>Detections</th><th>Monitored</th></tr></thead>
          <tbody>{lines}</tbody>
        </table>
      </div>
      {detail}
    </div>
  );
}

export default Trips;
