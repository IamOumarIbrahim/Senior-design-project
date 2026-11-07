//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

import { useState } from "react";
import { login } from "./api.js";
import Icon from "./Icon.jsx";

function Login(props) {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function send(e) {
    e.preventDefault();
    login(name, password).then(function (res) {
      if (res.error != undefined) {
        setError(res.error);
      } else {
        props.onDone(res.token, res.name);
      }
    });
  }

  return (
    <div className="login">
      <form className="card" onSubmit={send}>
        <div className="brand">
          <div className="logo"><Icon name="car" size={24} colour="#2f80ed" /></div>
          <div><b>DriveSafe</b><span>Stay alert. Stay safe.</span></div>
        </div>
        <label>Name</label>
        <input value={name} onChange={function (e) { setName(e.target.value); }} />
        <label>Password</label>
        <input type="password" value={password} onChange={function (e) { setPassword(e.target.value); }} />
        <div className="err">{error}</div>
        <button type="submit">Log in</button>
      </form>
    </div>
  );
}

export default Login;
