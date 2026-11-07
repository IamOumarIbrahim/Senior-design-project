//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

function Privacy() {
  return (
    <div className="page">
      <div className="head"><div><h1>Privacy &amp; data</h1><p>What we keep and what we never send</p></div></div>
      <div className="card text">
        <h3>What leaves the car</h3>
        <p>Only event records: the time, what was detected, how sure the system was, how long it lasted and the alert tier.</p>
        <h3>What never leaves the car</h3>
        <p>No video, no images and no face data. All video is processed on the device and is not saved by default. Your PIN also stays in the car.</p>
        <h3>Who can see it</h3>
        <p>Only you, when you log in to your own account. Data is sent over an encrypted connection.</p>
      </div>
    </div>
  );
}

export default Privacy;
