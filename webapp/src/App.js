import Neon, { wallet, rpc, tx, u, sc, Signer } from "@cityofzion/neon-js";
import { useEffect, useState } from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";

import "./App.css";
import DoraConnector from "./DoraConnector";
import Footer from "./navigation/Footer";
import Navigation from "./navigation/Navigation";
import About from "./screens/About";
import PlaceBet from "./screens/PlaceBet";
import Results from "./screens/Results";

import hero1 from "./1.jpg";
import hero2 from "./2.jpg";
import hero3 from "./3.png";
import hero4 from "./4.png";
const images = [hero1, hero2, hero3, hero4];

export const FLYBY_CONTRACT = "0xa9ab4ea48570270b4c4c9b47a97340f545dfd9a8";

function App() {
  const [invokeDetected, setInvokeDetected] = useState(false);
  const [randomImage, setRandomImage] = useState("");

  useEffect(() => {
    setRandomImage(images[Math.floor(Math.random() * images.length)]);
  }, [invokeDetected]);

  return (
    <div className="App bg-darkGrey flex flex-col h-screen justify-between">
      <Router>
        <div>
          <Navigation />
        </div>
        <main
          className={`mb-auto h-full ${
            invokeDetected ? "animate-flicker" : ""
          }`}
          style={
            invokeDetected
              ? {
                  backgroundImage: "url(" + randomImage + ")",
                  backgroundPosition: "center",
                  backgroundSize: "contain",
                  backgroundRepeat: "repeat",
                }
              : {}
          }
        >
          <DoraConnector setInvokeDetected={setInvokeDetected} />

          <div>
            {!invokeDetected && (
              <Switch>
                <Route path="/place-bet">
                  <PlaceBet />
                </Route>

                <Route path="/results">
                  <Results />
                </Route>

                <Route path="/">
                  <About />
                </Route>
              </Switch>
            )}
          </div>
        </main>
      </Router>
      <Footer />
    </div>
  );
}

export default App;
