"use strict";
document.addEventListener("DOMContentLoaded", () => {
  // =========================================================
  // TASTEMATCH CONFIGURATION
  // =========================================================

  // FastAPI runs on the same origin as the website.
const API_URL = "/api/restaurants?limit=100";

  const DATASET_CUISINES = [
    "American",
    "Chinese",
    "French",
    "Indian",
    "Italian",
    "Japanese",
    "Mexican",
    "Thai",
  ];

  const DATASET_PRICES = ["$", "$$", "$$$", "$$$$"];

  const DATASET_LOCATIONS = [
    "Chicago",
    "Houston",
    "Los Angeles",
    "New York",
    "San Francisco",
  ];

  // =========================================================
  // HTML ELEMENTS
  // =========================================================

  const searchForm = document.querySelector("#search-form");
  const searchInput = document.querySelector("#search-input");
  const cuisineSelect = document.querySelector("#cuisine");
  const priceSelect = document.querySelector("#price");
  const locationSelect = document.querySelector("#location");

  const resultsGrid = document.querySelector("#results-grid");
  const resultsTitle = document.querySelector("#results-title");
  const resultsCount = document.querySelector("#results-count");
  const resultsStatus = document.querySelector("#results-status");

  const clearButton = document.querySelector("#reset-filters");

  const mobileMenuButton = document.querySelector("#menu-toggle");
  const mobileMenu = document.querySelector("#mobile-nav");

  const currentYear = document.querySelector("#current-year");

  // allRestaurants contains real records returned by FastAPI.
  let allRestaurants = [];
  let isLoading = false;
  let requestController = null;

  // =========================================================
  // PROFESSIONAL BUTTON AND STATUS STYLES
  // =========================================================

  // These styles ensure the Clear filters button looks polished
  // even if styles.css does not yet contain a reset-button rule.
  const extraStyles = document.createElement("style");

  extraStyles.textContent = `
    .restaurant-search-form {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      align-items: end;
    }

    .restaurant-search-form .search-field {
      display: flex;
      flex-direction: column;
      gap: 8px;
      min-width: 0;
    }

    .restaurant-search-form label {
      font-size: 0.88rem;
      font-weight: 600;
    }

    .restaurant-search-form input,
    .restaurant-search-form select {
      box-sizing: border-box;
      width: 100%;
      min-height: 48px;
      padding: 12px 14px;
      border: 1px solid #d8cfc5;
      border-radius: 10px;
      background: #fffdf9;
      color: #332b28;
      font: inherit;
      transition: border-color 180ms ease, box-shadow 180ms ease;
    }

    .restaurant-search-form input:focus,
    .restaurant-search-form select:focus {
      outline: none;
      border-color: #722f37;
      box-shadow: 0 0 0 3px rgba(114, 47, 55, 0.12);
    }

    .restaurant-search-form .search-button,
    .restaurant-search-form .reset-button {
      box-sizing: border-box;
      display: inline-flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      min-height: 48px;
      padding: 12px 20px;
      border-radius: 10px;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 180ms ease, color 180ms ease,
                  border-color 180ms ease, transform 180ms ease,
                  box-shadow 180ms ease;
    }

    .restaurant-search-form .search-button {
      border: 1px solid #722f37;
      background: #722f37;
      color: #ffffff;
    }

    .restaurant-search-form .search-button:hover {
      background: #5c252c;
      border-color: #5c252c;
      box-shadow: 0 5px 14px rgba(114, 47, 55, 0.16);
      transform: translateY(-1px);
    }

    .restaurant-search-form .reset-button {
      border: 1px solid #d8cfc5;
      background: #f8f3ec;
      color: #722f37;
    }

    .restaurant-search-form .reset-button:hover {
      border-color: #722f37;
      background: #efe3dc;
      box-shadow: 0 4px 12px rgba(50, 35, 30, 0.07);
      transform: translateY(-1px);
    }

    .restaurant-search-form .search-button:focus-visible,
    .restaurant-search-form .reset-button:focus-visible {
      outline: 3px solid rgba(114, 47, 55, 0.3);
      outline-offset: 3px;
    }

    .restaurant-search-form button:disabled {
      opacity: 0.65;
      cursor: wait;
      transform: none;
      box-shadow: none;
    }

    .quick-searches {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 20px;
    }

    .quick-chip {
      cursor: pointer;
      transition: background 180ms ease, border-color 180ms ease;
    }

    .quick-chip:hover {
      border-color: #722f37;
      background: #efe3dc;
    }

    .restaurant-card {
      min-width: 0;
      overflow: hidden;
      border: 1px solid #e6ddd3;
      border-radius: 14px;
      background: #fffdf9;
      box-shadow: 0 4px 16px rgba(46, 34, 29, 0.045);
      transition: transform 180ms ease, box-shadow 180ms ease;
    }

    .restaurant-card:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 26px rgba(46, 34, 29, 0.09);
    }

    .restaurant-card-content {
      padding: 22px;
    }

    .restaurant-name {
      margin: 0 0 8px;
      color: #332b28;
      font-family: "Playfair Display", Georgia, serif;
      font-size: 1.25rem;
      overflow-wrap: anywhere;
    }

    .restaurant-cuisine {
      margin: 0 0 18px;
      color: #766960;
      font-size: 0.92rem;
    }

    .restaurant-details {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      color: #594b45;
      font-size: 0.85rem;
    }

    .restaurant-details span {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .restaurant-price {
      padding: 4px 8px;
      border-radius: 6px;
      background: #f2e9df;
      color: #722f37;
      font-weight: 700;
    }

    .restaurant-rating {
      color: #80551e;
      font-weight: 600;
    }

    .restaurant-status,
    .restaurant-empty-message {
      grid-column: 1 / -1;
      padding: 22px;
      border: 1px solid #e6ddd3;
      border-radius: 12px;
      background: #fffdf9;
      color: #594b45;
      line-height: 1.6;
    }

    .restaurant-status-error {
      border-color: #d8a9a9;
      background: #fff6f5;
      color: #842b2b;
    }

    .restaurant-status-success {
      color: #355d42;
    }

    .restaurant-status a {
      color: inherit;
      font-weight: 600;
      text-decoration: underline;
    }

    .results-count:not([hidden]) {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 30px;
      padding: 7px 12px;
      border-radius: 999px;
      background: #efe3dc;
      color: #722f37;
      font-size: 0.85rem;
      font-weight: 700;
    }

    @media (max-width: 640px) {
      .restaurant-search-form {
        grid-template-columns: minmax(0, 1fr);
      }

      .restaurant-search-form .search-button,
      .restaurant-search-form .reset-button {
        width: 100%;
      }

      .restaurant-card-content {
        padding: 18px;
      }
    }
  `;

  document.head.appendChild(extraStyles);

  // =========================================================
  // GENERAL UTILITIES
  // =========================================================

  function normalizeText(value) {
    return String(value ?? "").trim().toLocaleLowerCase();
  }

  function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
      element.className = className;
    }

    if (text !== undefined) {
      element.textContent = text;
    }

    return element;
  }

  function setStatus(message, type = "info") {
    if (resultsGrid) {
      resultsGrid.replaceChildren();

      const status = createElement(
        "p",
        `restaurant-status restaurant-status-${type}`,
        message
      );

      status.setAttribute(
        "role",
        type === "error" ? "alert" : "status"
      );

      resultsGrid.appendChild(status);
    }

    if (resultsStatus) {
      resultsStatus.textContent = "";
    }

    if (resultsCount) {
      resultsCount.hidden = true;
      resultsCount.textContent = "";
    }
  }

  function setResultsCount(count) {
    if (!resultsCount) return;

    resultsCount.textContent =
      `${count} ${count === 1 ? "restaurant" : "restaurants"}`;

    resultsCount.hidden = false;
  }

  // =========================================================
  // DROPDOWNS
  // =========================================================

  function populateSelect(select, values, placeholder) {
    if (!select) return;

    const previousValue = select.value;
    const fragment = document.createDocumentFragment();

    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = placeholder;

    fragment.appendChild(defaultOption);

    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      fragment.appendChild(option);
    });

    select.replaceChildren(fragment);

    if (values.includes(previousValue)) {
      select.value = previousValue;
    }
  }

  // The CSV values are the expected options. After loading the API,
  // options are rebuilt from the records actually returned by it.
  populateSelect(cuisineSelect, DATASET_CUISINES, "All cuisines");
  populateSelect(priceSelect, DATASET_PRICES, "All prices");
  populateSelect(locationSelect, DATASET_LOCATIONS, "All locations");

  // =========================================================
  // API RESPONSE HANDLING
  // =========================================================

  function extractRestaurants(data) {
    if (Array.isArray(data)) {
      return data;
    }

    if (Array.isArray(data?.restaurants)) {
      return data.restaurants;
    }

    if (Array.isArray(data?.items)) {
      return data.items;
    }

    if (Array.isArray(data?.results)) {
      return data.results;
    }

    if (Array.isArray(data?.data)) {
      return data.data;
    }

    return null;
  }

  
function normalizeRestaurant(restaurant) {
  const rawPrice =
    restaurant.price_range ?? restaurant.price_level;

  let priceRange = "Price not specified";

  if (typeof rawPrice === "string" && rawPrice.trim()) {
    priceRange = rawPrice.trim();
  } else if (rawPrice !== null && rawPrice !== undefined && rawPrice !== "") {
    const priceLevel = Number(rawPrice);

    if (Number.isInteger(priceLevel) && priceLevel >= 1 && priceLevel <= 4) {
      priceRange = "$".repeat(priceLevel);
    }
  }

  const rawRating = restaurant.rating ?? restaurant.average_rating;
  const numericRating = Number(rawRating);

  return {
    restaurant_id: String(
      restaurant.restaurant_id ?? restaurant.id ?? ""
    ),
    name: restaurant.name ?? "Restaurant",
    cuisine:
      restaurant.cuisine ?? restaurant.categories ?? "Cuisine not specified",
    rating:
      rawRating !== null &&
      rawRating !== undefined &&
      rawRating !== "" &&
      Number.isFinite(numericRating) &&
      numericRating > 0
        ? numericRating
        : null,
    price_range: priceRange,
    location:
      restaurant.location ?? restaurant.city ?? "Location not specified",
  };
}


  function rebuildDropdownsFromData(restaurants) {
    const uniqueValues = (field) => [
      ...new Set(
        restaurants
          .map((restaurant) => restaurant[field])
          .filter((value) => value !== "")
      ),
    ].sort((a, b) => a.localeCompare(b));

    populateSelect(
      cuisineSelect,
      uniqueValues("cuisine"),
      "All cuisines"
    );

    populateSelect(
      priceSelect,
      uniqueValues("price_range"),
      "All prices"
    );

    populateSelect(
      locationSelect,
      uniqueValues("location"),
      "All locations"
    );
  }

  // =========================================================
  // FILTERING
  // =========================================================

  function getFilters() {
    return {
      search: searchInput?.value.trim() ?? "",
      cuisine: cuisineSelect?.value ?? "",
      price: priceSelect?.value ?? "",
      location: locationSelect?.value ?? "",
    };
  }

  function filterRestaurants(restaurants, filters) {
    const search = normalizeText(filters.search);

    return restaurants.filter((restaurant) => {
      const matchesSearch =
        !search ||
        normalizeText(restaurant.name).includes(search) ||
        normalizeText(restaurant.cuisine).includes(search) ||
        normalizeText(restaurant.location).includes(search);

      const matchesCuisine =
        !filters.cuisine ||
        normalizeText(restaurant.cuisine) ===
          normalizeText(filters.cuisine);

      const matchesPrice =
        !filters.price ||
        normalizeText(restaurant.price_range) ===
          normalizeText(filters.price);

      const matchesLocation =
        !filters.location ||
        normalizeText(restaurant.location) ===
          normalizeText(filters.location);

      return (
        matchesSearch &&
        matchesCuisine &&
        matchesPrice &&
        matchesLocation
      );
    });
  }

  // =========================================================
  // RESTAURANT CARDS
  // =========================================================

  function createRestaurantCard(restaurant) {
    const card = createElement("article", "restaurant-card");
    const content = createElement("div", "restaurant-card-content");

    const name = createElement(
      "h3",
      "restaurant-name",
      restaurant.name
    );

    const cuisine = createElement(
      "p",
      "restaurant-cuisine",
      restaurant.cuisine || "Cuisine not specified"
    );

    const details = createElement("div", "restaurant-details");

    const location = createElement(
      "span",
      "restaurant-location",
      `⌖ ${restaurant.location || "Location not specified"}`
    );

    const price = createElement(
      "span",
      "restaurant-price",
      restaurant.price_range || "Price not specified"
    );

    const ratingText =
      restaurant.rating === null
        ? "Not rated"
        : `${restaurant.rating.toFixed(1)} / 5`;

    const rating = createElement(
      "span",
      "restaurant-rating",
      `★ ${ratingText}`
    );

    details.append(location, price, rating);
    content.append(name, cuisine, details);
    card.appendChild(content);

    return card;
  }

  function renderRestaurants(restaurants) {
    if (!resultsGrid) {
      console.error(
        'TasteMatch: missing element with id="results-grid".'
      );
      return;
    }

    resultsGrid.replaceChildren();

    if (resultsTitle) {
      resultsTitle.textContent = "Restaurants for you";
    }

    setResultsCount(restaurants.length);

    if (restaurants.length === 0) {
      resultsGrid.appendChild(
        createElement(
          "p",
          "restaurant-empty-message",
          "No restaurants match your selection. Try another cuisine, price range, location, or search term."
        )
      );

      if (resultsStatus) {
        resultsStatus.textContent =
          "Try clearing one or more filters to see more restaurants.";
      }

      return;
    }

    if (resultsStatus) {
      resultsStatus.textContent =
        "Showing matching restaurants from the connected dataset.";
    }

    const fragment = document.createDocumentFragment();

    restaurants.forEach((restaurant) => {
      fragment.appendChild(createRestaurantCard(restaurant));
    });

    resultsGrid.appendChild(fragment);
  }

  function applyFilters() {
    if (allRestaurants.length === 0) return;

    const filtered = filterRestaurants(
      allRestaurants,
      getFilters()
    );

    // Show higher-rated restaurants first. Keep unrated records last.
    filtered.sort((a, b) => {
      const ratingA = a.rating ?? -1;
      const ratingB = b.rating ?? -1;

      return ratingB - ratingA;
    });

    renderRestaurants(filtered);
  }

  // =========================================================
  // CONNECT FRONTEND TO FASTAPI
  // =========================================================

  async function loadRestaurants() {
    if (isLoading) return;

    isLoading = true;

    if (resultsTitle) {
      resultsTitle.textContent = "Loading restaurants...";
    }

    setStatus(
      "Connecting to the TasteMatch restaurant..."
    );

    if (clearButton) {
      clearButton.disabled = true;
    }

    // Cancel an older request if one exists.
    if (requestController) {
      requestController.abort();
    }

    requestController = new AbortController();

    try {
      const response = await fetch(API_URL, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
        signal: requestController.signal,
      });

      if (!response.ok) {
        throw new Error(
          `Restaurant API error: HTTP ${response.status}.`
        );
      }

      const data = await response.json();
      const records = extractRestaurants(data);

      if (records === null) {
        throw new Error(
          "The API response does not contain a restaurant list. Expected a JSON array or an object containing restaurants, items, results, or data."
        );
      }

      allRestaurants = records
        .filter((record) => record && typeof record === "object")
        .map(normalizeRestaurant)
        .filter((restaurant) => restaurant.name !== "");

      if (allRestaurants.length === 0) {
        setStatus(
          "We're sorry, but restaurant recommendations are temporarily unavailable. Please try again in a moment.",
          "error"
        );

        if (resultsTitle) {
          resultsTitle.textContent = "No restaurant data available";
        }

        return;
      }

      // Ensure dropdowns only contain values present in the records
      // that the backend actually returned.
      rebuildDropdownsFromData(allRestaurants);

      if (resultsTitle) {
        resultsTitle.textContent = "Restaurants for you";
      }

      applyFilters();

      console.info(
        `TasteMatch connected successfully: ${allRestaurants.length} restaurant records loaded from ${API_URL}.`
      );
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }

      console.error("TasteMatch could not load restaurant data:", error);

      allRestaurants = [];

      if (resultsTitle) {
        resultsTitle.textContent = "Restaurants are unavailable";
      }

      setStatus(
  "We're sorry, but restaurant recommendations are temporarily unavailable. Please try again in a moment.",
  "error"
      );
    } finally {
      isLoading = false;

      if (clearButton) {
        clearButton.disabled = false;
      }
    }
  }

  // =========================================================
  // SEARCH FORM
  // =========================================================

  if (searchForm) {
    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();

      applyFilters();

      document.querySelector("#results")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  // Apply filters immediately when dropdown values change.
  [cuisineSelect, priceSelect, locationSelect].forEach((select) => {
    select?.addEventListener("change", applyFilters);
  });

  // Search while the user types.
  searchInput?.addEventListener("input", applyFilters);

  // =========================================================
  // CLEAR FILTERS BUTTON
  // =========================================================

  if (clearButton) {
    clearButton.type = "button";
    clearButton.classList.add("reset-button");
    clearButton.textContent = "Clear filters";

    clearButton.addEventListener("click", () => {
      if (searchInput) {
        searchInput.value = "";
      }

      if (cuisineSelect) {
        cuisineSelect.value = "";
      }

      if (priceSelect) {
        priceSelect.value = "";
      }

      if (locationSelect) {
        locationSelect.value = "";
      }

      applyFilters();

      // Keep the interaction accessible and visible.
      clearButton.blur();
    });
  }

  // =========================================================
  // QUICK SEARCH CHIPS
  // =========================================================

  document.querySelectorAll("[data-search]").forEach((button) => {
    button.addEventListener("click", () => {
      const query = button.dataset.search ?? "";

      if (searchInput) {
        searchInput.value = query;
      }

      applyFilters();

      document.querySelector("#results")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  });

  // =========================================================
  // MOBILE NAVIGATION
  // =========================================================

  if (mobileMenuButton && mobileMenu) {
    mobileMenuButton.addEventListener("click", () => {
      const expanded =
        mobileMenuButton.getAttribute("aria-expanded") === "true";

      mobileMenuButton.setAttribute(
        "aria-expanded",
        String(!expanded)
      );

      mobileMenuButton.setAttribute(
        "aria-label",
        expanded ? "Open navigation" : "Close navigation"
      );

      mobileMenu.hidden = expanded;
    });

    mobileMenu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        mobileMenu.hidden = true;

        mobileMenuButton.setAttribute("aria-expanded", "false");
        mobileMenuButton.setAttribute(
          "aria-label",
          "Open navigation"
        );
      });
    });
  }

  // =========================================================
  // FOOTER
  // =========================================================

  if (currentYear) {
    currentYear.textContent = new Date().getFullYear();
  }

  // =========================================================
  // INITIALIZE
  // =========================================================

  if (!resultsGrid) {
    console.error(
      'TasteMatch cannot start: add <div id="results-grid"></div> to index.html.'
    );
    return;
  }

  loadRestaurants();
});