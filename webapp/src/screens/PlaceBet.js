import { useState, useEffect } from "react";
import Neon, { wallet, rpc, tx, u, sc, Signer } from "@cityofzion/neon-js";
import Select from "react-select";

import { FLYBY_CONTRACT } from "../App";

const { addFees, setBlockExpiry } = Neon.experimental.txHelpers;
const CONNECT = "CONNECT";
const BET = "BET";
const CONFIRM = "CONFIRM ";
const NODE_URL = "https://testnet1.neo.coz.io";

function Connect({ handleUpdateStep, setWif }) {
  const [wif, updateWifInput] = useState("");
  useEffect(() => {
    if (wallet.isWIF(wif)) {
      handleUpdateStep(BET);
      setWif(wif);
    }
  }, [wif, handleUpdateStep, setWif]);

  return (
    <div className="max-w-screen">
      <h1 className="text-2xl font-bold text-left italic">STEP 1:</h1>
      <p className="text-left mt-2">
        {" "}
        Connect your wallet to the daPP by using wallet connect or by entering
        in your private key below:{" "}
      </p>
      <input
        onChange={(e) => updateWifInput(e.target.value)}
        type="text"
        placeholder="Enter private key here..."
        class="px-3 py-3 relative bg-white bg-white rounded text-sm border-0 shadow outline-none focus:outline-none focus:ring focus:ring-highlight w-full"
      />
    </div>
  );
}

function Bet({ config, handleUpdateStep, passOptionInfo }) {
  const [pools, setPools] = useState([]);
  const [pool, setPool] = useState(null);
  const [option, setOption] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function parsePoolData({ value }) {
    const data = value[0].value;
    console.log({ data });

    // [pool_id, pool_creator_account, pool_description, pool_options, pool_result]
    const parsedPoolData = {
      name: atob(data[2].value),
      options: data[3].value.map(({ value }) => {
        return {
          id: value,
          label: atob(value),
        };
      }),
      id: data[0].value,
    };

    return parsedPoolData;
  }

  useEffect(() => {
    async function getPools() {
      setLoading(true);
      try {
        const contract = new Neon.experimental.SmartContract(
          Neon.u.HexString.fromHex(FLYBY_CONTRACT),
          {
            networkMagic: config.networkMagic,
            rpcAddress: config.nodeUrl,
            account: config.fromAccount,
          }
        );
        const results = await contract.testInvoke("list_on_going_pools", []);

        const pools = results.stack.map(parsePoolData);
        console.log("getPools() results: ", { results, pools });

        setPools(pools);
        setLoading(false);
      } catch (e) {
        setLoading(false);
        console.error({ e });
      }
    }
    getPools();
  }, [config]);

  function handleSelectPool(pool) {
    const selectedPool = pools.find(({ name }) => name === pool.label);
    setPool(selectedPool);
  }

  function handleSelectOption(option) {
    setOption(option);
  }

  async function placeBet() {
    setLoading(true);
    try {
      const rpcClient = new rpc.RPCClient(config.nodeUrl);
      const betConfig = {
        networkMagic: config.networkMagic,
        rpcAddress: config.nodeUrl,
        account: config.fromAccount,
      };
      const builder = new sc.ScriptBuilder();
      builder.emitAppCall(FLYBY_CONTRACT, "bet", [
        {
          type: "Hash160",
          value: config.fromAccount.scriptHash,
        },
        {
          type: "ByteArray",
          value: pool.id,
        },
        {
          type: "String",
          value: option.label,
        },
      ]);
      const transaction = new tx.Transaction();
      transaction.script = u.HexString.fromHex(builder.build());
      await setBlockExpiry(transaction, betConfig);
      transaction.addSigner({
        account: config.fromAccount.scriptHash,
        scopes: "Global",
      });
      await addFees(transaction, betConfig);
      transaction.sign(config.fromAccount, config.networkMagic);
      await rpcClient.sendRawTransaction(transaction);
      setLoading(false);
      handleUpdateStep(CONFIRM);
      passOptionInfo({ poolName: pool.name, option: option.label });
    } catch (e) {
      setLoading(false);
      console.error({ e });
      setError(e.message);
    }
  }

  return (
    <div className="max-w-screen">
      <h1 className="text-2xl font-bold text-left italic">STEP 2:</h1>
      {loading ? (
        <p className="mt-5"> Submitting data to the blockchain... </p>
      ) : (
        <div className="mt-5">
          <small className="flex text-left mb-1 text-lightGrey opacity-75">
            ADDRESS:
          </small>

          <a
            className="flex text-highlight cursor-pointer text-left mb-5"
            target="_blank"
            href={`https://dora.coz.io/address/neo3/mainnet/${config.fromAccount.address}`}
          >
            {config.fromAccount.address}
          </a>
          <small className="flex text-left mb-1 text-lightGrey opacity-75">
            BETTING POOL:
          </small>
          <Select
            isSearchable={false}
            value={
              pool
                ? {
                    value: pool.id,
                    label: pool.name,
                  }
                : null
            }
            getOptionValue={(option) => option.id}
            onChange={handleSelectPool}
            placeholder="Select pool..."
            options={pools.map((pool) => ({
              value: pool.id,
              label: pool.name,
            }))}
          />
          <br />
          <small className="flex text-left mb-1 text-lightGrey opacity-75">
            BET:
          </small>
          <Select
            isSearchable={false}
            value={option}
            onChange={handleSelectOption}
            placeholder="Select option..."
            isDisabled={!pool}
            options={pool ? pool.options : []}
            getOptionValue={(option) => option.id}
          />
          {error && <p className="text-red-500 text-sm mt-4">{error}</p>}
          <button
            onClick={placeBet}
            disabled={(!pool && !option) || error}
            className={`bg-highlight text-white font-bold py-2 px-4 rounded mt-7 disabled:opacity-50 ${
              !pool && !option ? "cursor-not-allowed" : "cursor-pointer"
            }`}
          >
            PLACE BET
          </button>
        </div>
      )}
    </div>
  );
}

function Confirm({ config, selectedOptionInfo }) {
  return (
    <div className="max-w-screen">
      <h1 className="text-2xl font-bold text-left italic">STEP 3:</h1>
      <p className="text-left mt-2">
        <span className="text-3xl">🎉 🎉 🎉 🎉 🎉 🎉 🎉</span>
        <br />
        <br />
        <a
          className="text-highlight cursor-pointer text-left mb-5"
          target="_blank"
          href={`https://dora.coz.io/address/neo3/mainnet/${config.fromAccount.address}`}
        >
          {config.fromAccount.address}
        </a>{" "}
        has bet on "{selectedOptionInfo.option}" for betting pool "
        {selectedOptionInfo.poolName}". Good luck!
      </p>
    </div>
  );
}

function PlaceBet() {
  const [currentStep, setCurrentStep] = useState(CONNECT);
  const [wif, setWif] = useState("");
  const [selectedOptionInfo, setSelectedOptionInfo] = useState({
    poolName: "",
    option: "",
  });

  const config = {
    fromAccount: wif && new wallet.Account(wif),
    tokenScriptHash: FLYBY_CONTRACT,
    amountToTransfer: 0.1,
    systemFee: 0,
    networkFee: 0,
    networkMagic: 844378958,
    nodeUrl: NODE_URL,
  };

  function returnCurrentStepContent(step) {
    switch (true) {
      case step === CONNECT:
        return <Connect handleUpdateStep={setCurrentStep} setWif={setWif} />;
      case step === BET:
        return (
          <Bet
            handleUpdateStep={setCurrentStep}
            config={config}
            passOptionInfo={({ poolName, option }) =>
              setSelectedOptionInfo({ poolName, option })
            }
          />
        );
      case step === CONFIRM:
        return (
          <Confirm selectedOptionInfo={selectedOptionInfo} config={config} />
        );
      default:
        return <Connect handleUpdateStep={setCurrentStep} setWif={setWif} />;
    }
  }

  return (
    <div className="max-w-screen-md m-auto bg-mediumGrey p-12 rounded-md mt-10">
      {returnCurrentStepContent(currentStep)}
    </div>
  );
}

export default PlaceBet;
