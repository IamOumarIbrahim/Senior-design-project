//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { useEffect, useState } from "react";
import { getData } from "./api.js";
import Icon from "./Icon.jsx";

function Tips(props) {
  const [tips, setTips] = useState(null);

  useEffect(function () {
    getData("/api/v1/tips", props.token, props.onLogout).then(function (d) {
      setTips(d);
    });
  }, []);

  if (tips == null) {
    return <div className="card">Loading ...</div>;
  }

  const rows = [];
  for (let i = 0; i < tips.length; i++) {
    rows.push(
      <div className="tip" key={i}>
        <div className="ic" style={{ background: "#fff4e2" }}><Icon name="bulb" size={16} colour="#f5a524" /></div>
        <div>{tips[i].text}<small>{tips[i].day}</small></div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="head"><div><h1>Tips</h1><p>Advice from your own trips</p></div></div>
      <div className="card">{rows}</div>
    </div>
  );
}

export default Tips;
