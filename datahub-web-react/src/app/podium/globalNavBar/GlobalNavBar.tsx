import React from "react";
import classes from "./GlobalNavBar.module.scss";


import { WaffleApp } from "@podium-ui/core-web";
import { Logo } from "@podium-ui/core-web";
import { L0NavBar } from "@podium-ui/shared-web";

import { L0MenuObj, Application } from "./types";

export type GlobalNavBarProps = {
  variant: "full" | "thin";
  currentAppPath: string;
  currentAppName: string;
  currentAppCode: string;
  appsData: Application[];
  /**
   * Passing undefined notification data will remove the notification icon and panel
   */
  goHome: Function;
  /**
   * This is required as we need to use Envision's routing because it's not compatible with the current implementation
   */
  menuData?: L0MenuObj;
  availableBusinessContext?: string[];
};

export const GlobalNavBar = ({
  variant = "full",
  currentAppPath,
  currentAppName,
  currentAppCode,
  appsData,
  goHome,
  menuData,
  availableBusinessContext = []
}: GlobalNavBarProps) => {
  return (
    <div className={`${classes.GlobalNavBar} ${classes[variant]}`}>
      <div className={classes.logo}>
        <Logo variant={variant} appDisplayName={currentAppName} goHome={goHome} currentAppPath={currentAppPath} />
      </div>
      <div className={classes.appSwitcher}>
        <WaffleApp variant={variant} metadata={appsData} currentAppCode={currentAppCode} />
      </div>
      <div className={classes.businessContextSwitcher}>
          {/* <L0NavBar
            metadata={menuData}
            path={window.location.pathname}
            availableBusinessContext={availableBusinessContext}
            variant={variant}
          /> */}
      </div>
      {/* <div className={classes.accountOptions}>
      </div>       */}
    </div>
  );
};
