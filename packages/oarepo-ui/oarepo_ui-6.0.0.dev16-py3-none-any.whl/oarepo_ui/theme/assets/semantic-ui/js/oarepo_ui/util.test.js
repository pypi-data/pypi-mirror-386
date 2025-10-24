import {
  getInputFromDOM,
  scrollTop,
  object2array,
  array2object,
  requiredMessage,
  unique,
  scrollToElement,
  getLocalizedValue,
  encodeUnicodeBase64,
  decodeUnicodeBase64,
  timestampToRelativeTime,
} from "./util";
import { i18next } from "@translations/oarepo_ui/i18next";
import * as Yup from "yup";

describe("scrollToElement", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("should call scrollIntoView on element with matching id", () => {
    const div = document.createElement("div");
    div.id = "my.path";
    div.scrollIntoView = jest.fn();
    document.body.appendChild(div);
    scrollToElement("my.path");
    expect(div.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "center",
    });
  });

  it("should call scrollIntoView on label with matching for attribute", () => {
    const label = document.createElement("label");
    label.setAttribute("for", "my.label");
    label.scrollIntoView = jest.fn();
    document.body.appendChild(label);
    scrollToElement("my.label");
    expect(label.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "center",
    });
  });

  it("should not throw if no matching element exists", () => {
    expect(() => scrollToElement("missing.path")).not.toThrow();
  });
});

describe("getInputFromDOM", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("should return parsed value from input element with name and value", () => {
    const input = document.createElement("input");
    input.setAttribute("name", "testField");
    input.setAttribute("value", JSON.stringify({ foo: "bar" }));
    document.body.appendChild(input);
    const result = getInputFromDOM("testField");
    expect(result).toEqual({ foo: "bar" });
  });

  it("should return null if element does not exist", () => {
    expect(getInputFromDOM("missingField")).toBeNull();
  });

  it("should return null if element has no value attribute", () => {
    const input = document.createElement("input");
    input.setAttribute("name", "noValue");
    document.body.appendChild(input);
    expect(getInputFromDOM("noValue")).toBeNull();
  });
});

describe("object2array", () => {
  it("should transform object to array of objects", () => {
    const obj = { en: "English", fr: "Français" };
    const result = object2array(obj, "lang", "title");
    expect(result).toEqual([
      { lang: "en", title: "English" },
      { lang: "fr", title: "Français" },
    ]);
  });

  it("should return empty array for empty object", () => {
    const obj = {};
    const result = object2array(obj, "lang", "title");
    expect(result).toEqual([]);
  });
});

describe("array2object", () => {
  it("should transform array of objects to object", () => {
    const arr = [
      { lang: "en", title: "English" },
      { lang: "fr", title: "Français" },
    ];
    const result = array2object(arr, "lang", "title");
    expect(result).toEqual({ en: "English", fr: "Français" });
  });

  it("should return empty object for empty array", () => {
    const arr = [];
    const result = array2object(arr, "lang", "title");
    expect(result).toEqual({});
  });

  it("should return empty object for non-array input", () => {
    const notArray = null;
    const result = array2object(notArray, "lang", "title");
    expect(result).toEqual({});

    const notArray2 = undefined;
    expect(array2object(notArray2, "lang", "title")).toEqual({});

    const notArray3 = {};
    expect(array2object(notArray3, "lang", "title")).toEqual({});

    const notArray4 = 42;
    expect(array2object(notArray4, "lang", "title")).toEqual({});
  });
});

describe("requiredMessage", () => {
  it("should return required message", () => {
    const label = "Name";
    const msg = requiredMessage({ label });
    expect(msg).toContain(label);
    expect(msg).toContain("is a required field");
  });
});

describe("encodeUnicodeBase64 / decodeUnicodeBase64", () => {
  it("should encode and decode unicode base64", () => {
    const str = "čřž";
    const encoded = encodeUnicodeBase64(str);
    const decoded = decodeUnicodeBase64(encoded);
    expect(decoded).toBe(str);
  });
});

describe("unique", () => {
  it("should return true for empty or single item", () => {
    expect(unique([], {}, "lang", "error")).toBe(true);
    expect(unique([{ lang: "en" }], {}, "lang", "error")).toBe(true);
  });
  it("should return ValidationError for duplicates", () => {
    const arr = [
      { lang: "en", value: 1 },
      { lang: "en", value: 2 },
    ];
    const result = unique(arr, { path: "arr" }, "lang", "Duplicate");
    expect(result).toBeInstanceOf(Yup.ValidationError);
    expect(result.errors).toEqual(
      expect.arrayContaining([expect.stringContaining("Duplicate")])
    );
  });
});

describe("scrollTop", () => {
  it("should call window.scrollTo", () => {
    window.scrollTo = jest.fn();
    scrollTop();
    expect(window.scrollTo).toHaveBeenCalledWith({
      top: 0,
      left: 0,
      behavior: "smooth",
    });
  });
});

describe("timestampToRelativeTime", () => {
  it("should return a string for valid ISO timestamp", () => {
    const now = new Date().toISOString();
    const result = timestampToRelativeTime(now);
    expect(typeof result).toBe("string");
  });

  it("should handle invalid timestamp gracefully", () => {
    const result = timestampToRelativeTime("not-a-date");
    expect(result === null || typeof result === "string").toBe(true);
  });

  it("should return correct format for past timestamp", () => {
    i18next.language = "en";
    const past = new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString();
    const result = timestampToRelativeTime(past);
    expect(typeof result).toBe("string");
    expect(result).toMatch(/ago|days?/i);
  });

  it("should return correct format for future timestamp", () => {
    i18next.language = "en";
    const future = new Date(Date.now() + 1000 * 60 * 60 * 24 * 3).toISOString();
    const result = timestampToRelativeTime(future);
    expect(typeof result).toBe("string");
    expect(result).toMatch(/in|days?/i);
  });

  it("should handle non-date input without throwing", () => {
    expect(() => timestampToRelativeTime(12345)).not.toThrow();
    expect(() => timestampToRelativeTime({})).not.toThrow();
    expect(timestampToRelativeTime(12345)).toBeNull();
    expect(timestampToRelativeTime({})).toBeNull();
  });
});

describe("getLocalizedValue", () => {
  beforeEach(() => {
    i18next.language = "cs";
    i18next.options = { fallbackLng: "en" };
  });

  const multilingualObject = {
    cs_CZ: "Nazdar světe",
    cs: "Ahoj světe",
    en: "Hello world",
    fr: "Bonjour le monde",
    und: "Undefined",
  };

  const multilingualArray = [
    { lang: "cs_CZ", value: "Nazdar světe" },
    { lang: "cs", value: "Ahoj světe" },
    { lang: "en", value: "Hello world" },
    { lang: "fr", value: "Bonjour le monde" },
    { lang: "und", value: "Undefined" },
  ];

  test.each([
    ["object", multilingualObject],
    ["array", multilingualArray],
  ])("returns exact locale match for %s input", (_type, input) => {
    i18next.language = "cs_CZ";
    expect(getLocalizedValue(input)).toBe("Nazdar světe");
  });

  test.each([
    ["object", multilingualObject],
    ["array", multilingualArray],
  ])("returns base language match for %s input", (_type, input) => {
    i18next.language = "cs_SK"; // not defined, but base 'cs' is
    expect(getLocalizedValue(input)).toBe("Ahoj světe");
  });

  test.each([
    ["object", multilingualObject],
    ["array", multilingualArray],
  ])("returns fallbackLng match for %s input", (_type, input) => {
    i18next.language = "de";
    i18next.options.fallbackLng = "en";
    expect(getLocalizedValue(input)).toBe("Hello world");
  });

  test.each([
    ["object", multilingualObject],
    ["array", multilingualArray],
  ])(
    "returns 'en' match if fallbackLng missing for %s input",
    (_type, input) => {
      i18next.language = "de";
      delete i18next.options.fallbackLng;
      expect(getLocalizedValue(input)).toBe("Hello world");
    }
  );

  test.each([
    ["object", multilingualObject],
    ["array", multilingualArray],
  ])(
    "returns any available non-'und' value if no match for %s input",
    (_type, input) => {
      i18next.language = "it";
      const values = [
        { lang: "es", value: "Hola" },
        { lang: "und", value: "Undefined" },
      ];
      expect(getLocalizedValue(values)).toBe("Hola"); // first defined - en
    }
  );

  test.each([
    ["object", { und: "Undefined" }],
    ["array", [{ lang: "und", value: "Undefined" }]],
  ])("returns 'und' if no other value exists for %s input", (_type, input) => {
    i18next.language = "ru";
    expect(getLocalizedValue(input)).toBe("Undefined");
  });

  test.each([
    ["object", {}],
    ["array", []],
  ])("returns null for empty %s input", (_type, input) => {
    expect(getLocalizedValue(input)).toBeNull();
  });
});
