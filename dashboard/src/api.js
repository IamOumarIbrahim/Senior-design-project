//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

// all calls to the server go through here

export function getData(path, token, onLoggedOut) {
  return fetch(path, {
    headers: { Authorization: "Bearer " + token }
  }).then(function (res) {
    if (res.status == 401) {
      onLoggedOut();
      return null;
    }
    return res.json();
  });
}

export function login(name, password) {
  return fetch("/api/v1/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name, password: password })
  }).then(function (res) {
    return res.json().then(function (body) {
      if (res.status != 200) {
        return { error: body.detail };
      }
      return body;
    });
  });
}
