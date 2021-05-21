import { useEffect, useState } from "react";

import { FLYBY_CONTRACT } from "./App";

function DoraConnector({ setInvokeDetected = () => null }) {
  const [currentBlock, setCurrenBlock] = useState(0);
  useEffect(() => {
    const socket = new WebSocket(
      `wss://dora.coz.io/ws/v1/neo3/testnet/log/${FLYBY_CONTRACT}`
    );
    socket.onmessage = function (event) {
      console.log("incoming socket event:", { event });
      const data = JSON.parse(event.data);
      setCurrenBlock(data.height);
      if (
        data.log &&
        data.log.notifications.find((e) => e.event_name === "ChangeImage")
      ) {
        setInvokeDetected(true);
        setTimeout(() => {
          setInvokeDetected(false);
        }, 7500);
      }
    };
  });

  return (
    <code className="bg-darkGrey">
      {" "}
      websocket connection to dora:{" "}
      {currentBlock === 0 ? <b>dead</b> : <b>live</b>}
      <br /> current block height: {currentBlock}
    </code>
  );
}

export default DoraConnector;
