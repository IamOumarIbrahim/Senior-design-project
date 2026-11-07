//   Senior Design Project - Edge-Cloud Driver Monitoring (Group 34)
//        Oumar Mamoun Ibrahim U22200741
//        Abdullah Jafar Abdelhamid U23101327
//        Faris Munadhil Ahmed Alagha U23104246
//        Mohamed Ahmed Saad Khafagy U20101649

// the icon function comes from public/icons.js, same icons as the tablet

function Icon(props) {
  let width = 2;
  if (props.width != undefined) {
    width = props.width;
  }
  const svg = window.icon(props.name, props.size, props.colour, width);
  return <span className="icon" dangerouslySetInnerHTML={{ __html: svg }} />;
}

export default Icon;
