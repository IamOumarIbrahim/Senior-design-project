//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { useEffect, useState } from "react";
import { getData } from "./api.js";
import Icon from "./Icon.jsx";
import Login from "./Login.jsx";
import Overview from "./Overview.jsx";
import Privacy from "./Privacy.jsx";
import Statistics from "./Statistics.jsx";
import Tips from "./Tips.jsx";
import Trips from "./Trips.jsx";

const PAGES = [
  ["Dashboard", "home"],
  ["Trips", "map"],
  ["Statistics", "bars"],
  ["Tips", "bulb"],
  ["Privacy & data", "shield"]
];

function App() {
  const [token, setToken] = useState(sessionStorage.getItem("token"));
  const [name, setName] = useState(sessionStorage.getItem("name"));
  const [page, setPage] = useState("Dashboard");
  const [data, setData] = useState(null);
  const [week, setWeek] = useState(null);

  function logout() {
    sessionStorage.clear();
    setToken(null);
    setData(null);
  }

  function loggedIn(t, n) {
    sessionStorage.setItem("token", t);
    sessionStorage.setItem("name", n);
    setName(n);
    setToken(t);
  }

  useEffect(function () {
    if (token != null) {
      let path = "/api/v1/summary";
      if (week != null) {
        path = path + "?week=" + week;
      }
      getData(path, token, logout).then(function (d) {
        setData(d);
      });
    }
  }, [token, week]);

  if (token == null) {
    return <Login onDone={loggedIn} />;
  }

  // Left menu
  const links = [];
  for (let i = 0; i < PAGES.length; i++) {
    let cls = "";
    let colour = "#4a5565";
    if (PAGES[i][0] == page) {
      cls = "on";
      colour = "#2f80ed";
    }
    links.push(
      <a key={PAGES[i][0]} className={cls} onClick={function () { setPage(PAGES[i][0]); }}>
        <Icon name={PAGES[i][1]} size={20} colour={colour} />
        {PAGES[i][0]}
      </a>
    );
  }

  let body = <div className="card">Loading ...</div>;
  if (data != null) {
    if (data.empty) {
      body = <div className="card">No trips yet. Your trips show up here after the first upload.</div>;
    } else if (page == "Dashboard") {
      body = <Overview data={data} setWeek={setWeek} />;
    } else if (page == "Trips") {
      body = <Trips token={token} onLogout={logout} />;
    } else if (page == "Statistics") {
      body = <Statistics data={data} />;
    } else if (page == "Tips") {
      body = <Tips token={token} onLogout={logout} />;
    } else {
      body = <Privacy />;
    }
  }

  let upload = "";
  if (data != null && data.empty == false) {
    upload = data.last_upload.substring(11, 16);
  }

  return (
    <div className="body">
      <div className="nav">
        <div className="brand">
          <div className="logo"><Icon name="car" size={24} colour="#2f80ed" /></div>
          <div><b>DriveSafe</b><span>Stay alert. Stay safe.</span></div>
        </div>
        {links}
        <div className="mon">
          <span style={{ color: "#27ae60" }}>●</span> Last trip {upload}
          <small>Event records only · TLS · no video</small>
        </div>
        <div className="who">{name} <button onClick={logout}>Log out</button></div>
      </div>
      <div className="main">{body}</div>
    </div>
  );
}

export default App;
