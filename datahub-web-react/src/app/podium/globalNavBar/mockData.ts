import { Application } from "@podium-ui/core-web/molecules/Waffle/WaffleAllApp";

export const applications: Application[] = [
  {
    id: 2,
    applicationName: "Self Service Analytics",
    applicationCode: "SELFSERVICE",
    path: "/",
    icon: "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCABAAEADASIAAhEBAxEB/8QAGwAAAwEAAwEAAAAAAAAAAAAAAAUHBgMECAH/xAA4EAABAgQDBAgDBwUAAAAAAAABAgMABAURBgcSEyExQRQyUWFxgZGxFUKhFhciI6LB0UNScpLw/8QAGAEAAwEBAAAAAAAAAAAAAAAAAAEDBAL/xAAdEQACAgIDAQAAAAAAAAAAAAABAgARAxIhMUFR/9oADAMBAAIRAxEAPwCzQQQQQhHG9MMyzZcfebaQPmWoJHqYQ41xUjCtF6QlKXJp46JdtXAm28nuH8RH5Om4mx9UHHkqcm1JP43Xl6W278hyHgIqmPYWTQk2ejQ7l8l5uWm0lUtMNPJHEtrCh9I5o8/1TDGJcFuNzy9bKb2TMyrpIB7CRvHnFPy9xmrE8i5LTukVCVAKykWDqf7rcu/y7Yb4qGwNiCvZozYwQQRGUhBBBBCSDOZbhrlPbN9mJYqT4lRv7CO9RhPryg04bK+mh5XSAwfzOtvtbffTp77QwzdoqpyhsVRpN1yS7OWH9NXPyIHqYl9DxLVsOvKcpk2poL66CApCvEGNiDbGK8mZjq5uUSkJqzWWVa+1G3DRQro6Zu+0G7d1t/Wta8ZnKpx1GN2Utk6XGXEueFr+4EKK7i+t4jQluozeplJuGkJCUX7SBx842uTlGVtZ2tOJISE9HaJHE7io/RPqYbDVCT7EDswqVWCCCMU1QggjE1/NKi0h5ctKIXUX0bjslBLYPZq5+QMdKpbgREgdzYTUszOyjsrMIC2nkFC0nmCLGPO2J6A/huuP094EoB1MrPzoPA/9zEbj7w8aVf8AFSKDZo8FIl1u/q4Q2n6FUscYQT8Wp6pKtyhOyWsBId/gH6ERdLxnmRenHEk1KpkzWKmxT5RGt59WlPYO0nuA3x6MotJl6HSJamyw/LYRa/NR4knxNzGHwphedwhh2Yq/w5U3W30aWpdNiWgeAPufC0Lvtzj2lDXU6EXGk9ZS5VaP1DdDyXkNLBKTkyrwRgKLm5SZ5xLNTlnKetRttNWtvzNgR6RvW3EOtpcbWlaFgFKkm4IPMGM7KV7lQwPU4Z+V6bT5mU2imtu0pvWninUCLj1iKppNby+qi5qaokvUZcbg+traItfiD8h8YuUEdI+vETJtJ1JZyUlxAE7TZqXVz2RS4ketvaGreaeFFpuqcebPYqXX+wMPZ3DVDqJKpukyjqlcVlkavXjCteXGEXDdVHSP8X3B7Kh3jPhip/s6680cJpFxPOr7hLr/AHELZvOKiNJPRZGcmFctQShJ87k/SHKctsIINxRx5vun3VDGTwnh6QIVLUeTQocFFoKUPM3MF4x4YU8k1QcrOY08hVPw6xLpCrl9CLf7uGwPha8VzDdJXQsPSdMcf265dFlL7SSTu7hew7hDMAAAAWA4AR9hO+wodRqlG5//2Q==",
    logo: "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",
  },
];

export const navigationMetaData = 
{
  menu: [
    {
      id: 1,
      menuName: "Analytics",
      link: "/analytics",
      subMenus: [],
      externalLink: "",
      subMenuEndpoint: "",
      subMenuLink: "",
      subMenuTitle: "",
      sourcePages: [],
      appCode: "",
      createdDate: "",
      createdBy: "",
      lastModifiedDate: "",
      lastModifiedBy: ""
    },
    {
      id: 2,
      menuName: "Glossary",
      link: "/glossary",
      subMenus: [],
      externalLink: "",
      subMenuEndpoint: "",
      subMenuLink: "",
      subMenuTitle: "",
      sourcePages: [],
      appCode: "",
      createdDate: "",
      createdBy: "",
      lastModifiedDate: "",
      lastModifiedBy: ""
    }
  ]
}