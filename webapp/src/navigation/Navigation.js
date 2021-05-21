import React from "react";
import { Link, NavLink } from "react-router-dom";

import DesktopLogo from "./desktop_logo.png";
import logo from "./logo.svg";
import "./Navigation.css";

function Navigation({ fixed }) {
  const [navbarOpen, setNavbarOpen] = React.useState(false);
  return (
    <>
      <nav className="relative flex flex-wrap items-center justify-between px-2 py-3 mb-3 border-b border-highlight bg-darkGrey pb-5">
        <div className="container px-4 mx-auto flex flex-wrap items-center justify-between">
          <div className="w-full relative flex justify-between lg:w-auto lg:static lg:block lg:justify-start">
            <div className="flex items-end">
              <Link to={"/"}>
                <img
                  className="desktop-navigation cursor-pointer"
                  src={DesktopLogo}
                />
              </Link>
              <a href={"https://neo.org/"} target="_blank">
                <img
                  className="desktop-navigation-n3-logo ml-1 -mb-1 cursor-pointer"
                  src={logo}
                />
              </a>
            </div>
            <button
              className="text-white cursor-pointer text-xl leading-none px-3 py-1 border border-solid border-transparent rounded bg-transparent block lg:hidden outline-none focus:outline-none"
              type="button"
              onClick={() => setNavbarOpen(!navbarOpen)}
            >
              <i className="fas fa-bars"></i>
            </button>
          </div>
          <div
            className={
              "lg:flex flex-grow items-center" +
              (navbarOpen ? " flex" : " hidden")
            }
            id="example-navbar-danger"
          >
            <ul className="flex flex-col lg:flex-row list-none lg:ml-auto">
              <li className="nav-item primary-nav-item">
                <NavLink
                  exact
                  className="px-3 py-2 flex items-center text-xs uppercase font-bold leading-snug text-white hover:opacity-75"
                  to="/"
                  activeClassName="border-b-2 border-highlight rounded-sm"
                >
                  <span className="ml-2">About</span>
                </NavLink>
              </li>
              <li className="nav-item primary-nav-item">
                <NavLink
                  exact
                  className="px-3 py-2 flex items-center text-xs uppercase font-bold leading-snug text-white hover:opacity-75"
                  to="/place-bet"
                  activeClassName="border-b-2 border-highlight rounded-sm"
                >
                  <span className="ml-2">Place bet</span>
                </NavLink>
              </li>
              <li className="nav-item primary-nav-item">
                <NavLink
                  exact
                  className="px-3 py-2 flex items-center text-xs uppercase font-bold leading-snug text-white hover:opacity-75"
                  to="/results"
                  activeClassName="border-b-2 border-highlight rounded-sm"
                >
                  <span className="ml-2">Results</span>
                </NavLink>
              </li>
              <li className="nav-item">
                <a
                  className="px-3 py-2 flex items-center text-xs uppercase font-bold leading-snug text-white hover:opacity-75"
                  href="#pablo"
                >
                  <i className="fab fa-github text-lg leading-lg text-white opacity-75"></i>
                  <span className="ml-2">github </span>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </>
  );
}

export default Navigation;
