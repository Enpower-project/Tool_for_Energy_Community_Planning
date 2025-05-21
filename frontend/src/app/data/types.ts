import { EXTERNAL_ROUTES } from "./externalRoutes"
import { APP_ROUTES } from "./routes"

/**
 *
 * @export
 * @interface CardInfo
 * @typedef {CardInfo}
 */
export interface CardInfo {
    id?: number,
    /**
     * icon url 
     *
     * @type {string}
     */
    iconName: string,
    /**
     * card title
     *
     * @type {string}
     */
    title: string,
    /**
     * card description
     *
     * @type {?string}
     */
    description?: string,
    /**
     * card subtitle
     *
     * @type {?string}
     */
    subtitle?: string,
    /**
     * card final title icon
     *
     * @type {boolean}
     */
    infoIcon: boolean
    /**
     * Valid if the card is hide
     *
     * @type {?boolean}
     */
    show?: boolean;

    info?: string;

    validate?: boolean;

    disableiconName?: string;

    parentID?:number
}

/**
 *
 * @export
 * @interface achievementCard
 * @typedef {achievementCard}
 */
export interface achievementCard {
    /**
     * icon url 
     *
     * @type {string}
     */
    iconName: string,
    /**
     * card title
     *
     * @type {string}
     */
    title: string,
    /**
     * Valid if card is disabled
     *
     * @type {?boolean}
     */
    disabled?: boolean
    /**
     * Valid if card is complete
     *
     * @type {?boolean}
     */
    complete?: boolean
}


/**
 * Array of cards to be used in the create scenario module
 *
 * @type {CardInfo[]}
 */
export const cardArrayModule: CardInfo[] = [
    {
        id: 1,
        iconName: 'wind_turbines.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.MORE_RENEWABLE_ENERGY.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.MORE_RENEWABLE_ENERGY.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.MORE_RENEWABLE_ENERGY.BODY',
        infoIcon: true
    },
    {
        id: 3,
        iconName: 'collective_self_consumption.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.SELF_SUFFICIENCY.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.SELF_SUFFICIENCY.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.SELF_SUFFICIENCY.BODY',
        infoIcon: true
    },
    {
        id: 2,
        iconName: 'voltage_reactive_power_control.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.HIGHER_EFFICIENCY.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.HIGHER_EFFICIENCY.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.HIGHER_EFFICIENCY.BODY',
        infoIcon: true
    },
    {
        id: 6,
        iconName: 'v2g_services.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.E_MOBILITY.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.E_MOBILITY.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.E_MOBILITY.BODY',
        infoIcon: true
    },
    {
        id: 5,
        iconName: 'electric_load.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.ELECTRIFICATION.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.ELECTRIFICATION.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.ELECTRIFICATION.BODY',
        infoIcon: true
    },
    {
        id: 4,
        iconName: 'blackout_strategies.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.DECARBONISATION.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.DECARBONISATION.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.DECARBONISATION.BODY',
        infoIcon: true
    },
    {
        id: 7,
        iconName: 'tree_localres.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.OTHER.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.OTHER.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.OTHER.BODY',
        infoIcon: true
    },
    {
        id: 7,
        iconName: 'support_technical_execution.svg',
        title: 'CREATE_SCENARIOS.GOAL_MENU.GUIDED.GOAL',
        description: 'CREATE_SCENARIOS.GOAL_MENU.GUIDED.CAPTION',
        info: 'CREATE_SCENARIOS.GOAL_MENU.GUIDED.BODY',
        show: false,
        infoIcon: true
    },

]

/**
 * Array of cards to be used in the welcome module
 *
 * @type {CardInfo[]}
 */
export const cardBussinessArray: CardInfo[] = [
    {
        iconName: 'chevron-right-black.svg',
        title: 'ONBOARDING.OPTIONS.NEW_COMMUNITY',
        infoIcon: false,
        disableiconName: 'chevron-right-disable.svg',
    },
    {
        iconName: 'chevron-right-black.svg',
        title: 'ONBOARDING.OPTIONS.ACCESS_RESULTS',
        infoIcon: false,
        disableiconName: 'chevron-right-disable.svg',
    },
    {
        iconName: 'chevron-right-black.svg',
        title: 'ONBOARDING.OPTIONS.ACADEMY',
        infoIcon: false,
        disableiconName: 'chevron-right-disable.svg',
    },
    {
        iconName: 'chevron-right-black.svg',
        title: 'ONBOARDING.OPTIONS.EXPERT',
        infoIcon: false,
        disableiconName: 'chevron-right-disable.svg',
    },
]

/**
 * Array of cards to be used in the knowledge centre
 *
 * @type {CardInfo[]}
 */
export const cardGlossaryArray: CardInfo[] = [
    {
        iconName: 'books-blue.svg',
        title: 'RESOURCES.USEFUL_RESOURCES.H1',
        description: 'RESOURCES.USEFUL_RESOURCES.D1',
        infoIcon: false
    },
    {
        iconName: 'books-blue.svg',
        title: '',
        description: '',
        infoIcon: false
    },
]

/**
 * Array of glossary names to be used in the knowledge centre
 *
 * @type {*}
 */
export const glossaryItems: any = {
    ENERGY_COMMUNITIES: [
        "ENERGY_COMMUNITY",
        "RENEWABLE_ENERGY",
        "MICROGRID",
        "SMART_GRID",
        "CARBON_FOOTPRINT",
        "ALTERNATIVE",
        "MEMBER",
        "SINGLE_FAMILY_HOUSE",
        "MULTI_FAMILY_HOUSE",
        "APARTMENT BLOCK",
        "OFFICE",
        "COMMERCIAL",
        "PUBLIC",
        "NET_METERING",
        "ENERGY_STORAGE",
        "PEER-TO-PEER-ENERGY-TRADING",
        "VPP",
        "EMS",
        "GRID-INDEPENDENCE",
        "ENERGY-EFFICIENCY",
        "DATA-ANALYTICS",
        "CONTEXT",
        "DELIVERED_ENERGY",
        "DELIVERY_NODE",
        "ENERGY_ASSET",
        "ENERGY_SYSTEM",
        "KPI",
        "MODELLING",
        "NETWORK_SIZING",
        "PLANNING_TOOL",
    ],
    GOALS: [
        'MORE_RENEWABLES',
        'SELF_SUFFICIENCY',
        'HIGHER_EFFICIENCY',
        'E_MOBILITY',
        'ELECTRIFICATION',
        'DECARBONISATION'
    ],
    ACTIONS: [
        'REDUCTION_OF_DEMAND',
        'DEMAND_RESPONSE',
        'SOLAR_FLEET',
        'WIND_OFFSHORE_FLEET',
        'HYDRO_FLEET',
        'GEOTHERMAL_FLEET',
        'SOLAR_THERMAL',
        'BIOMASS_BOILER',
        'GAS_BOILER',
        'HEAT_PUMP',
        'GEOTHERMAL_HEAT',
        'METHANISATION',
        'GAS_CHP',
        'BATTERY_STORAGE',
        'HEAT_STORAGE',
        'GAS_STORAGE',
        'CREATION_DHN',
        'CONEECTION_TO_DHN',
        'DHN_SUPPLIER',
        'CHARGING_STATION',
        'GRID',
        'DC',
        'ELECTRIC_HEATER',
        'OTHER',
        'OIL_BOILER',
        'HYDROGEN'
    ]

}

/**
 * Array of cards to be used in the our community module
 *
 * @type {achievementCard[]}
 */
export const achivementCardArray: achievementCard[] = [
    {
        iconName: "check-green.svg",
        title: "COMMUNITY.PROGRESS.CREATE_COMMUNITY",
        complete: true
    },
    {
        iconName: "play.svg",
        title: "COMMUNITY.PROGRESS.REFINE",
    },
    {
        iconName: "play.svg",
        title: "COMMUNITY.PROGRESS.CREATE_COMMUNITY",
    },
    {
        iconName: "play.svg",
        title: "COMMUNITY.PROGRESS.CREATE_COMMUNITY",
    },
    {
        iconName: "lock-gray.svg",
        title: "COMMUNITY.PROGRESS.CREATE_COMMUNITY",
        disabled: true
    },
]

export interface NavigationControl {
    name: string,
    url: string,
    icon: string
    active: boolean
    urlType: NAV_URL_TYPE
    hover?: boolean;
    childs?: ChildsNavigation[],
};

export interface ChildsNavigation {
    name: string;
    icon: string;
    active: boolean;
    messageDisable: string;
    disable?: boolean;
    urlType: NAV_URL_TYPE;
    url: string;
    hover?: boolean;
    childs?: StepChildNavigation[];
    alternative?: NavigationControl
    id?: number,
};

export interface StepChildNavigation {
    name: string,
    active: boolean,
    url?: string,
};

export enum NAV_URL_TYPE {
    EXTERNAL, INTERNAL, FORMULARY, COMMUNITYURL
}

export const priNavigationMenu: NavigationControl[] =
    [
        {
            name: "MENU.DESKTOP.MENU.HOME",
            icon: "home-blue.svg",
            urlType: NAV_URL_TYPE.INTERNAL,
            url: APP_ROUTES.HOME,
            active: false,
        } as NavigationControl,
        {
            name: "MENU.DESKTOP.MENU.GET_STARTED.HEADING",
            icon: "star-blue.svg",
            urlType: NAV_URL_TYPE.INTERNAL,
            url: APP_ROUTES.FORMULARY,
            active: false,
            childs: [
                {
                    name: "MENU.DESKTOP.MENU.GET_STARTED.CREATE_A_COMMUNITY.HEADING",
                    urlType: NAV_URL_TYPE.FORMULARY,
                    url: {
                        steps: 1,
                        selectedCardWelcome: 0
                    },
                    active: false,
                    childs: [
                        {
                            name: "MENU.DESKTOP.MENU.GET_STARTED.CREATE_A_COMMUNITY.LOCATION",
                            active: false
                        },
                        {
                            name: "MENU.DESKTOP.MENU.GET_STARTED.CREATE_A_COMMUNITY.NUMBER_OF_BUILDINGS",
                            active: false
                        },
                        {
                            name: "MENU.DESKTOP.MENU.GET_STARTED.CREATE_A_COMMUNITY.PROFILE",
                            active: false
                        },
                        {
                            name: "MENU.DESKTOP.MY_COMMUNITY.SUMMARY",
                            active: false
                        },
                    ]
                },
                {
                    name: "MENU.DESKTOP.MENU.GET_STARTED.EXPLORE_MY_COMMUNITY.HEADING",
                    urlType: NAV_URL_TYPE.FORMULARY,
                    url: {
                        steps: 1,
                        selectedCardWelcome: 1
                    },
                    active: false,
                    childs: [
                        {
                            name: "MENU.DESKTOP.MENU.GET_STARTED.EXPLORE_MY_COMMUNITY.FIND",
                            active: false
                        },
                        {
                            name: "MENU.DESKTOP.MENU.GET_STARTED.EXPLORE_MY_COMMUNITY.PREVIEW",
                            active: false
                        },
                    ]
                },
                {
                    name: "MENU.DESKTOP.MENU.GET_STARTED.CREATE_ALTERNATIVES.HEADING",
                    urlType: NAV_URL_TYPE.FORMULARY,
                    url: {
                        steps: 1,
                        selectedCardWelcome: 2
                    },
                    active: false,
                    childs: undefined
                },
                {
                    name: "MENU.DESKTOP.MENU.GET_STARTED.LEARN_AND_RESEARCH",
                    urlType: NAV_URL_TYPE.INTERNAL,
                    url: APP_ROUTES.KNOWLDEDGE,
                    // urlType: NAV_URL_TYPE.FORMULARY,
                    // url: {
                    //     steps: 1,
                    //     selectedCardWelcome: 3
                    // } as any,
                    active: false,
                    childs: undefined
                },
            ]
        } as NavigationControl,
        {
            name: "MENU.MOBILE.FAQ",
            icon: "help-circle-blue.svg",
            urlType: NAV_URL_TYPE.INTERNAL,
            url: APP_ROUTES.FAQ
        } as NavigationControl,
        {
            name: "MENU.MOBILE.KNOWLEDGE_CENTRE",
            icon: "book-open-blue.svg",
            urlType: NAV_URL_TYPE.INTERNAL,
            url: APP_ROUTES.KNOWLDEDGE
        } as NavigationControl,
        {
            name: "MENU.MOBILE.ABOUT",
            icon: "map-pin-blue.svg",
            urlType: NAV_URL_TYPE.EXTERNAL,
            url: EXTERNAL_ROUTES.ABOUT_PROJECT
        } as NavigationControl,
    ]

export const secNavigationMenu: NavigationControl[] =
    [
        {
            name: "MENU.DESKTOP.MY_COMMUNITY.SUMMARY",
            icon: "bar-chart-2-blue.svg",
            urlType: NAV_URL_TYPE.COMMUNITYURL,
            url: APP_ROUTES.COMMUNITY,
            active: false,
            childs: []
        } as NavigationControl,
    ]


export interface AlternativeAction {
    id: number,
    name: string,
    controlName: string,
    translate: string,
};

export const AlternativesActionsArray: AlternativeAction[] =
    [
        {
            id: 1,
            name: "reduction_of_demand",
            controlName: "reductionDemand",
            translate: "REDUCTION_OF_DEMAND",
        } as AlternativeAction,
        {
            id: 2,
            name: "demand_response",
            controlName: "demandResponse",
            translate: "DEMAND_RESPONSE",
        } as AlternativeAction,
        {
            id: 3,
            name: "solar_fleet",
            controlName: "solarFleet",
            translate: "SOLAR_FLEET",
        } as AlternativeAction,
        {
            id: 4,
            name: "wind_offshore_fleet",
            controlName: "WindOffshoreFleet",
            translate: "WIND_OFFSHORE_FLEET",
        } as AlternativeAction,
        {
            id: 5,
            name: "hydro_fleet",
            controlName: "HydroFleet",
            translate: "HYDRO_FLEET"
        } as AlternativeAction,
        {
            id: 6,
            name: "geothermal_fleet",
            controlName: "GeothermalFleet",
            translate: "GEOTHERMAL_FLEET"
        } as AlternativeAction,
        {
            id: 7,
            name: "solar_thermal",
            controlName: "SolarThermal",
            translate: "SOLAR_THERMAL"
        } as AlternativeAction,
        {
            id: 8,
            name: "biomass_boiler",
            controlName: "BiomassBoiler",
            translate: "BIOMASS_BOILER"
        } as AlternativeAction,
        {
            id: 9,
            name: "gas_boiler",
            controlName: "GasBoiler",
            translate: "GAS_BOILER"
        } as AlternativeAction,
        {
            id: 10,
            name: "heat_pump",
            controlName: "HeatPump",
            translate: "HEAT_PUMP"
        } as AlternativeAction,
        {
            id: 11,
            name: "geothermal_heat",
            controlName: "GeothermalHeat",
            translate: "GEOTHERMAL_HEAT"
        } as AlternativeAction,
        {
            id: 12,
            name: "methanisation",
            controlName: "Methanisation",
            translate: "METHANISATION"
        } as AlternativeAction,
        {
            id: 13,
            name: "gas_chp",
            controlName: "GasCHPCombinedHeatandPower",
            translate: "GAS_CHP",
        } as AlternativeAction,
        // {
        //     id: 14,
        //     name: "biomass_chp",
        //     controlName: "BiomassCHPCombinedHeatandPower",
        //     translate: "Biomass CHP (Combined Heat and Power)"
        // } as AlternativeAction,
        {
            id: 15,
            name: "battery_storage",
            controlName: "BatteryStorage",
            translate: "BATTERY_STORAGE"
        } as AlternativeAction,
        {
            id: 16,
            name: "heat_storage",
            controlName: "HeatStorage",
            translate: "HEAT_STORAGE"
        } as AlternativeAction,
        {
            id: 17,
            name: "gas_storage",
            controlName: "GasStorage",
            translate: "GAS_STORAGE"
        } as AlternativeAction,
        {
            id: 18,
            name: "creation_of_dhn",
            controlName: "CreationofDHN",
            translate: "CREATION_DHN"
        } as AlternativeAction,
        {
            id: 19,
            name: "connection_to_the_dhn",
            controlName: "ConnectiontotheDHN",
            translate: "CONEECTION_TO_DHN"
        } as AlternativeAction,
        {
            id: 20,
            name: "dhn_supplier",
            controlName: "DHNSupplier",
            translate: "DHN_SUPPLIER"
        } as AlternativeAction,
        {
            id: 21,
            name: "charging_station",
            controlName: "ChargingStation",
            translate: "CHARGING_STATION"
        } as AlternativeAction,
        {
            id: 22,
            name: "grid",
            controlName: "Grid",
            translate: "GRID"
        } as AlternativeAction,
        // {
        //     id: 23,
        //     name: "DHN",
        //     controlName: "",
        //     translate: ""
        // } as AlternativeAction,
        {
            id: 24,
            name: "DC",
            controlName: "DC",
            translate: "DC"
        } as AlternativeAction,
        {
            id: 25,
            name: "electric_heater",
            controlName: "Electrification",
            translate: "ELECTRIC_HEATER"
        } as AlternativeAction,
        {
            id: 26,
            name: "other",
            controlName: "Other",
            translate: "OTHER"
        } as AlternativeAction,
        {
            id: 27,
            name: "oil_boiler",
            controlName: "OilBoiler",
            translate: "OIL_BOILER"
        } as AlternativeAction,
        {
            id: 28,
            name: "hydrogen",
            controlName: "Hydrogen",
            translate: "HYDROGEN"
        } as AlternativeAction,
    ]


export interface UsefulResource {
    title: string;
    description: string;
    url?: string;
    icon?: string;
    image?: string;
    badgets?: string[];
};

export const UsefulResources: UsefulResource[] = [
    {
        title: "RESOURCES.USEFUL_RESOURCES.H1",
        description: "RESOURCES.USEFUL_RESOURCES.D1",
        badgets: ["RESOURCES.USEFUL_RESOURCES.BADGE.GOVERNANCE", "RESOURCES.USEFUL_RESOURCES.BADGE.PLANNING"],
        icon: "./assets/icons/europe.svg",
        url: "https://wayback.archive-it.org/12090/20240807073032/https://energy-communities-repository.ec.europa.eu/energy-communities-repository-energy-communities/energy-communities-repository-map_en",
        image: "./assets/images/resources-card-img1.png"
    } as UsefulResource,
    {
        title: "RESOURCES.USEFUL_RESOURCES.H2",
        description: "RESOURCES.USEFUL_RESOURCES.D2",
        badgets: ["RESOURCES.USEFUL_RESOURCES.BADGE.GOVERNANCE", "RESOURCES.USEFUL_RESOURCES.BADGE.LEGAL_POLITICAL"],
        icon: "./assets/icons/europe.svg",
        url: "",
        image: "./assets/images/resources-card-img2.png"
    } as UsefulResource,
    {
        title: "RESOURCES.USEFUL_RESOURCES.H3",
        description: "RESOURCES.USEFUL_RESOURCES.D3",
        badgets: ["RESOURCES.USEFUL_RESOURCES.BADGE.SOCIAL", "RESOURCES.USEFUL_RESOURCES.BADGE.PLANNING", "RESOURCES.USEFUL_RESOURCES.BADGE.LEGAL_POLITICAL", "RESOURCES.USEFUL_RESOURCES.BADGE.FINANCIAL",],
        icon: "./assets/icons/europe.svg",
        url: "",
        image: "./assets/images/resources-card-img3.png"
    } as UsefulResource,
    {
        title: "RESOURCES.USEFUL_RESOURCES.H4",
        description: "RESOURCES.USEFUL_RESOURCES.D4",
        badgets: ["RESOURCES.USEFUL_RESOURCES.BADGE.GOVERNANCE", "RESOURCES.USEFUL_RESOURCES.BADGE.LEGAL_POLITICAL"],
        icon: "./assets/icons/europe.svg",
        url: "",
        image: "./assets/images/resources-card-img4.png"
    } as UsefulResource,


]

/*

        <div>
      <dropdowntups [title]="'RESOURCES.GLOSSARY.ACTIONS.Electric Mobility.TERM'"
      [mainText]="'RESOURCES.GLOSSARY.ACTIONS.Electric Mobility.P1'"
      [subText]="'RESOURCES.GLOSSARY.ACTIONS.Electric Mobility.P2'" [smartDropdown]="true"></dropdowntups>
      <label class="check-tick">
        <input type="checkbox" formControlName="ElectricMobility" />
        <span class="checkmark"></span>
      </label>
    </div>
    <div>
      <dropdowntups [title]="'RESOURCES.GLOSSARY.ACTIONS.Electrification.TERM'"
      [mainText]="'RESOURCES.GLOSSARY.ACTIONS.Electrification.P1'"
      [subText]="'RESOURCES.GLOSSARY.ACTIONS.Electrification.P2'" [smartDropdown]="true"></dropdowntups>
      <label class="check-tick">
        <input type="checkbox" formControlName="Electrification" />
        <span class="checkmark"></span>
      </label>
    </div>
    <div>
      <dropdowntups [title]="'RESOURCES.GLOSSARY.ACTIONS.Energy Resilience.TERM'"
      [mainText]="'RESOURCES.GLOSSARY.ACTIONS.Energy Resilience.P1'"
      [subText]="'RESOURCES.GLOSSARY.ACTIONS.Energy Resilience.P2'" [smartDropdown]="true"></dropdowntups>
      <label class="check-tick">
        <input type="checkbox" formControlName="EnergyResilience" />
        <span class="checkmark"></span>
      </label>
    </div>
  </div>
*/