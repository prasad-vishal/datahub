export type GridDirection = 'row' | 'row-reverse' | 'column' | 'column-reverse';

export type Application = {
  id: number;
  applicationName: string;
  applicationCode: string;
  path: string;
  icon: string;
  logo: string;
};

export type AppPageObj = {
    id: number;
    pageName: string;
    pageDescription: string;
    link?: string;
  };

export type MenuItemObj = {
    id: number;
    menuName: string;
    link: string;
    subMenus: Array<MenuItemObj>;
    externalLink: string;
    subMenuEndpoint?: string;
    subMenuLink?: string;
    subMenuTitle?: string;
    subMenuOrientation?: GridDirection | undefined;
    sourcePages?: Array<AppPageObj>;
    appCode: string;
    createdDate: string;
    createdBy: string;
    lastModifiedDate: string;
    lastModifiedBy: string;
    setTitle?: (title: string) => {};
    pathArr?: number[];
    urlTemplate?: string;
    isGroupHeader?: boolean;
    ord?: number;
    isContextBack?: boolean;
  };


export type L0MenuObj = {
    backNavigation?: {
      id: string;
      label: string;
      path: string;
    };
    menu: MenuItemObj[];
} | null;