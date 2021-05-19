import Neon, { wallet } from "@cityofzion/neon-js";
import { useEffect, useState } from "react";
import { BrowserRouter as Router, Switch, Route, Link } from "react-router-dom";

import Logo from "./logo.svg";
import hero1 from "./1.jpg";
import hero2 from "./2.jpg";
import hero3 from "./3.png";
import Easel from "./easel.svg";
import "./App.css";

const images = [hero1, hero2, hero3];

function App() {
  const [currentBlock, setCurrenBlock] = useState(0);
  const [invokeDetected, setInvokeDetected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(
      `wss://dora.coz.io/ws/v1/neo3/testnet/log/0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381`
    );
    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      setCurrenBlock(data.height);
      if (
        data.log &&
        data.log.notifications.find((e) => e.event_name === "ChangeImage")
      ) {
        setInvokeDetected(true);
        setTimeout(() => {
          setInvokeDetected(false);
        }, 10000);
      }
    };
  });

  console.log({ invokeDetected });

  return (
    <div className="App">
      <img id="neo-logo" src={Logo} />
      <Router>
        <div>
          <nav>
            <code>
              {" "}
              websocket connection to dora live: current block height:{" "}
              {currentBlock}
            </code>
            <ul>
              <li>
                <Link to="/">Party time</Link>
              </li>
              <li>
                <Link to="/invoke-contract">Invoke Contract</Link>
              </li>
            </ul>
          </nav>

          {/* A <Switch> looks through its children <Route>s and
            renders the first one that matches the current URL. */}
          <Switch>
            <Route path="/invoke-contract">
              <Invoke />
            </Route>

            <Route path="/">
              <Home invokeDetected={invokeDetected} />
            </Route>
          </Switch>
        </div>
      </Router>
    </div>
  );
}

function Invoke() {
  const [wif, setWif] = useState("");
  const [isValidWif, setIsValidWif] = useState(false);
  const [processing, setProcessing] = useState(false);
  const nodeURL = "https://testnet1.neo.coz.io";

  useEffect(() => {
    if (wallet.isWIF(wif)) {
      setIsValidWif(true);
    }
  }, [wif]);

  async function performInvoke(inputs) {
    const contract = new Neon.experimental.SmartContract(
      Neon.u.HexString.fromHex("0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381"),
      {
        networkMagic: inputs.networkMagic,
        rpcAddress: inputs.nodeUrl,
        account: inputs.fromAccount,
      }
    );
    await contract.invoke("request_image_change", []);
  }

  async function handleInvoke() {
    const from = new wallet.Account(wif);
    const inputs = {
      fromAccount: from,
      tokenScriptHash: "0xf9ffa64482b38c0dc7841cf27d25a9f03dfb0381",
      amountToTransfer: 0.1,
      systemFee: 0,
      networkFee: 0,
      networkMagic: 844378958,
      nodeUrl: nodeURL,
    };

    setProcessing(true);
    performInvoke(inputs).then(() => {
      setProcessing(false);
    });
  }

  return (
    <>
      {processing ? (
        <div>
          <p>Invoking the smart contract...</p>
        </div>
      ) : isValidWif ? (
        <button onClick={handleInvoke}> CLICK TO INVOKE </button>
      ) : (
        <form>
          <input onChange={(e) => setWif(e.target.value)} type="text"></input>
          <input type="submit"></input>
        </form>
      )}
    </>
  );
}

function Home({ invokeDetected }) {
  return (
    <div id="frame-container">
      <div id="frame">
        {invokeDetected && (
          <img className="animate-flicker " src={hero1} id="hero" />
        )}
      </div>
    </div>
  );
}

export default App;
