import Neon, { wallet, rpc, tx, u, sc, Signer } from "@cityofzion/neon-js";
import { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Link,
  useHistory,
} from "react-router-dom";

import Logo from "./logo.svg";
import hero1 from "./1.jpg";
import hero2 from "./2.jpg";
import hero3 from "./3.png";
import hero4 from "./4.png";
import "./App.css";
const { addFees, setBlockExpiry } = Neon.experimental.txHelpers;
const FLYBY_CONTRACT = "0xa9ab4ea48570270b4c4c9b47a97340f545dfd9a8";

function App() {
  const [currentBlock, setCurrenBlock] = useState(0);
  const [invokeDetected, setInvokeDetected] = useState(false);

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
        }, 10000);
      }
    };
  });

  return (
    <div className="App">
      <a href="https://neo.org" target="_blank">
        <img id="neo-logo" src={Logo} alt="n3-logo" />
      </a>
      <Router>
        <div>
          <nav>
            <code>
              {" "}
              websocket connection to dora:{" "}
              {currentBlock === 0 ? <b>dead</b> : <b>live</b>} <br />
              <br /> current block height: {currentBlock}
            </code>
            <ul>
              <li>
                <Link to="/">View the blockchain powered easal</Link>
              </li>
              <li>
                <Link to="/invoke-contract">Invoke Contract</Link>
              </li>
            </ul>
          </nav>
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
  const [error, setError] = useState(false);
  const nodeURL = "https://testnet1.neo.coz.io";
  const history = useHistory();

  useEffect(() => {
    if (wallet.isWIF(wif)) {
      setIsValidWif(true);
    }
  }, [wif]);

  async function requestImageChange(inputs) {
    const contract = new Neon.experimental.SmartContract(
      Neon.u.HexString.fromHex(FLYBY_CONTRACT),
      {
        networkMagic: inputs.networkMagic,
        rpcAddress: inputs.nodeUrl,
        account: inputs.fromAccount,
      }
    );
    await contract.invoke("request_image_change", []);
  }

  async function getPools(inputs) {
    const contract = new Neon.experimental.SmartContract(
      Neon.u.HexString.fromHex(FLYBY_CONTRACT),
      {
        networkMagic: inputs.networkMagic,
        rpcAddress: inputs.nodeUrl,
        account: inputs.fromAccount,
      }
    );
    await contract.testInvoke("list_on_going_pools", []);
  }

  async function getPool(inputs) {
    const contract = new Neon.experimental.SmartContract(
      Neon.u.HexString.fromHex(FLYBY_CONTRACT),
      {
        networkMagic: inputs.networkMagic,
        rpcAddress: inputs.nodeUrl,
        account: inputs.fromAccount,
      }
    );
    await contract.testInvoke("get_pool", [
      {
        type: "ByteArray",
        value: "xOlaSCYnLhVN80Q/OFgOrf/T6Ej1vJovMn/Klg6XYaY=",
      },
    ]);
  }

  async function performBet(inputs) {
    const rpcClient = new rpc.RPCClient(inputs.nodeUrl);
    const config = {
      networkMagic: inputs.networkMagic,
      rpcAddress: inputs.nodeUrl,
      account: inputs.fromAccount,
    };
    const builder = new sc.ScriptBuilder();
    builder.emitAppCall(FLYBY_CONTRACT, "bet", [
      {
        type: "Hash160",
        value: inputs.fromAccount.scriptHash,
      },
      {
        type: "ByteArray",
        value: "xOlaSCYnLhVN80Q/OFgOrf/T6Ej1vJovMn/Klg6XYaY=",
      },
      {
        type: "String",
        value: "choice2",
      },
    ]);
    const transaction = new tx.Transaction();
    transaction.script = u.HexString.fromHex(builder.build());
    await setBlockExpiry(transaction, config);
    transaction.addSigner({
      account: inputs.fromAccount.scriptHash,
      scopes: "Global",
    });
    await addFees(transaction, config);
    transaction.sign(inputs.fromAccount, inputs.networkMagic);
    const results = await rpcClient.sendRawTransaction(transaction);
    console.log(results);
  }

  async function handleInvoke() {
    const from = new wallet.Account(wif);
    const inputs = {
      fromAccount: from,
      tokenScriptHash: FLYBY_CONTRACT,
      amountToTransfer: 0.1,
      systemFee: 0.1,
      networkFee: 0.1,
      networkMagic: 844378958,
      nodeUrl: nodeURL,
    };

    setProcessing(true);
    getPool(inputs)
      .then(() => {
        setProcessing(false);
        history.push("/");
      })
      .catch((e) => {
        console.error(e);
        setProcessing(false);
        setWif("");
        setIsValidWif(false);
        setError(e.message || e);
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
          {error && <code id="error"> {error} </code>}
          <label>Enter private key below to invoke contract:</label>
          <input onChange={(e) => setWif(e.target.value)} type="text"></input>
        </form>
      )}
    </>
  );
}

const images = [hero1, hero2, hero3, hero4];
function Home({ invokeDetected }) {
  const [randomImage, setRandomImage] = useState("");

  useEffect(() => {
    setRandomImage(images[Math.floor(Math.random() * images.length)]);
  }, [invokeDetected]);

  return (
    <div id="frame-container">
      <div id="frame">
        {invokeDetected && (
          <img
            className="animate-flicker "
            src={randomImage}
            id="hero"
            alt="flickering-hero"
          />
        )}
      </div>
    </div>
  );
}

export default App;
