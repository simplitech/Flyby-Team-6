import boa from "../boa.svg";
import dora from "../dora.svg";
import neonJs from "../neonjs.svg";

function Home() {
  return (
    <div className="max-w-screen-md m-auto bg-mediumGrey p-12 rounded-md mt-10">
      <p>
        <b className="italic text-xl mr-1">BET ON</b> is a decentralized
        application built on top of the NEO blockchain for the COZ “flyby
        hackathon”. Its purpose is to create a fun blockchain application that
        demonstrates the wide variety of development tools available to the
        community allowing developers to create virutally any dApp they can
        imagine on NEO.
      </p>
      <br />
      <p>
        This dApp was created by{" "}
        <a className="text-highlight" href="#">
          meevee98
        </a>
        ,{" "}
        <a className="text-highlight" href="#">
          rssavietto
        </a>{" "}
        and{" "}
        <a className="text-highlight" href="#">
          comountainclimber
        </a>
        . And leverages the following open source tools built by COZ:
      </p>
      <br />
      <div className="flex justify-evenly flex-wrap">
        <img className="cursor-pointer" src={boa} />
        <img className="cursor-pointer" src={dora} />
        <img className="cursor-pointer" src={neonJs} />
      </div>
    </div>
  );
}

export default Home;
