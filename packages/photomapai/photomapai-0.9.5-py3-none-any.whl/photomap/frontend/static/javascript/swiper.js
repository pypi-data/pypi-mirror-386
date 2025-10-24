// swiper.js
// This file initializes the Swiper instance and manages slide transitions.
import { eventRegistry } from "./event-registry.js";
import { toggleGridSwiperView } from "./events.js";
import { updateMetadataOverlay } from "./metadata-drawer.js";
import { fetchImageByIndex } from "./search.js";
import { getCurrentSlideIndex, slideState } from "./slide-state.js";
import { state } from "./state.js";
import { updateCurrentImageMarker } from "./umap.js";

export const initializeSingleSwiper = async () => {
  const swiperManager = new SwiperManager();
  swiperManager.initializeSingleSwiper();
  return swiperManager;
};

class SwiperManager {
  constructor() {
    if (SwiperManager.instance) {
      return SwiperManager.instance;
    }

    this.swiper = null;
    this.hasTouchCapability = this.isTouchDevice();
    this.isPrepending = false;
    this.isAppending = false;
    this.isInternalSlideChange = false;

    SwiperManager.instance = this;
  }

  // Check if the device is mobile
  isTouchDevice() {
    return (
      "ontouchstart" in window ||
      navigator.maxTouchPoints > 0 ||
      navigator.msMaxTouchPoints > 0
    );
  }

  isVisible() {
    const singleContainer = document.getElementById("singleSwiperContainer");
    return singleContainer && singleContainer.style.display !== "none";
  }

  async initializeSingleSwiper() {

    // Swiper config for single-image mode
    const swiperConfig = {
      direction: "horizontal",
      slidesPerView: 1,
      spaceBetween: 0,
      navigation: {
        prevEl: "#singleSwiperPrevButton",
        nextEl: "#singleSwiperNextButton",
      },
      autoplay: {
        delay: state.currentDelay * 1000,
        disableOnInteraction: false,
        enabled: false,
      },
      pagination: {
        el: ".swiper-pagination",
        clickable: true,
        dynamicBullets: true,
      },
      loop: false,
      touchEventsTarget: "container",
      allowTouchMove: true,
      simulateTouch: true,
      touchStartPreventDefault: false,
      touchMoveStopPropagation: false,
      keyboard: {
        enabled: true,
        onlyInViewport: true,
      },
      mousewheel: {
        enabled: true,
        releaseonEdges: true,
      },
    };

    if (this.hasTouchCapability) {
      swiperConfig.zoom = {
        maxRatio: 3,
        minRatio: 1,
        toggle: false,
        containerClass: "swiper-zoom-container",
        zoomedSlideClass: "swiper-slide-zoomed",
      };
    }

    // Initialize Swiper
    this.swiper = new Swiper("#singleSwiper", swiperConfig);
    state.swiper = this.swiper; // Keep state.swiper in sync for backward compatibility

    this.initializeSwiperHandlers();
    this.initializeEventHandlers();
    this.addDoubleTapHandlersToSlides();

    // Initial icon state and overlay
    this.updateSlideshowIcon();
    updateMetadataOverlay(this.currentSlide());
  }

  initializeSwiperHandlers() {
    if (!this.swiper) return;

    this.swiper.on("autoplayStart", () => {
      if (!state.gridViewActive) this.updateSlideshowIcon();
    });

    this.swiper.on("autoplayResume", () => {
      if (!state.gridViewActive) this.updateSlideshowIcon();
    });

    this.swiper.on("autoplayStop", () => {
      if (!state.gridViewActive) this.updateSlideshowIcon();
    });

    this.swiper.on("autoplayPause", () => {
      if (!state.gridViewActive) this.updateSlideshowIcon();
    });

    this.swiper.on("scrollbarDragStart", () => {
      if (!state.gridViewActive) this.pauseSlideshow();
    });

    this.swiper.on("slideChange", () => {
      if (this.isAppending || this.isPrepending || this.isInternalSlideChange)
        return;
      this.isInternalSlideChange = true;
      const activeSlide = this.swiper.slides[this.swiper.activeIndex];
      if (activeSlide) {
        const globalIndex = parseInt(activeSlide.dataset.globalIndex, 10) || 0;
        const searchIndex = parseInt(activeSlide.dataset.searchIndex, 10) || 0;
        slideState.updateFromExternal(globalIndex, searchIndex);
        updateMetadataOverlay(this.currentSlide());
      }
      this.isInternalSlideChange = false;
    });

    this.swiper.on("slideNextTransitionStart", () => {
      if (this.isAppending) return;

      if (this.swiper.activeIndex === this.swiper.slides.length - 1) {
        this.isAppending = true;
        this.swiper.allowSlideNext = false;

        const { globalIndex: nextGlobal, searchIndex: nextSearch } =
          slideState.resolveOffset(+1);

        if (nextGlobal !== null) {
          this.addSlideByIndex(nextGlobal, nextSearch)
            .then(() => {
              this.isAppending = false;
              this.swiper.allowSlideNext = true;
            })
            .catch(() => {
              this.isAppending = false;
              this.swiper.allowSlideNext = true;
            });
        } else {
          this.isAppending = false;
          this.swiper.allowSlideNext = true;
        }
      }
    });

    this.swiper.on("slidePrevTransitionEnd", () => {
      const [globalIndex] = getCurrentSlideIndex();
      if (this.swiper.activeIndex === 0 && globalIndex > 0) {
        const { globalIndex: prevGlobal, searchIndex: prevSearch } =
          slideState.resolveOffset(-1);
        if (prevGlobal !== null) {
          const prevExists = Array.from(this.swiper.slides).some(
            (el) => parseInt(el.dataset.globalIndex, 10) === prevGlobal
          );
          if (!prevExists) {
            this.isPrepending = true;
            this.swiper.allowSlidePrev = false;
            this.addSlideByIndex(prevGlobal, prevSearch, true)
              .then(() => {
                this.swiper.slideTo(1, 0);
                this.isPrepending = false;
                this.swiper.allowSlidePrev = true;
              })
              .catch(() => {
                this.isPrepending = false;
                this.swiper.allowSlidePrev = true;
              });
          }
        }
      }
    });

    this.swiper.on("sliderFirstMove", () => {
      this.pauseSlideshow();
    });
  }

  initializeEventHandlers() {
    // Stop slideshow on next and prev button clicks
    document
      .querySelectorAll(".swiper-button-next, .swiper-button-prev")
      .forEach((btn) => {
        eventRegistry.install(
          { type: "swiper", event: "click", object: btn },
          function (event) {
            state.single_swiper.pauseSlideshow();
            event.stopPropagation();
            this.blur();
          }
        );
        eventRegistry.install(
          { type: "swiper", event: "mousedown", object: btn },
          function (event) {
            this.blur();
          }
        );
      });

    // Reset slide show when the album changes
    eventRegistry.install({ type: "swiper", event: "albumChanged" }, () => {
      this.resetAllSlides();
    });

    // Reset slide show when the search results change
    eventRegistry.install(
      { type: "swiper", event: "searchResultsChanged" },
      () => {
        this.resetAllSlides();
      }
    );

    // Handle slideshow mode changes
    eventRegistry.install(
      { type: "swiper", event: "swiperModeChanged" },
      () => {
        this.resetAllSlides();
      }
    );

    // Navigate to a slide
    eventRegistry.install(
      { type: "swiper", event: "seekToSlideIndex" },
      (event) => this.seekToSlideIndex(event)
    );
  }

  addDoubleTapHandlersToSlides() {
    if (!this.swiper) return;
    // Attach handlers to all current slides
    this.swiper.slides.forEach((slideEl) => {
      this.attachDoubleTapHandler(slideEl);
    });
    // Attach handler to future slides (if slides are added dynamically)
    this.swiper.on("slideChange", () => {
      this.swiper.slides.forEach((slideEl) => {
        this.attachDoubleTapHandler(slideEl);
      });
    });
  }

  attachDoubleTapHandler(slideEl) {
    if (slideEl.dataset.doubleTapHandlerAttached) return;

    // Double-click (desktop)
    slideEl.addEventListener("dblclick", async () => {
      await toggleGridSwiperView(true);
    });

    // Double-tap (touch devices)
    let lastTap = 0;
    let tapCount = 0;

    // Prevent default on touchstart when it's a potential double-tap
    slideEl.addEventListener(
      "touchstart",
      (e) => {
        if (e.touches.length === 1) {
          tapCount++;
          if (tapCount === 2) {
            e.preventDefault(); // Prevent zoom on second tap
          }
          setTimeout(() => {
            tapCount = 0;
          }, 350);
        }
      },
      { passive: false }
    ); // passive: false allows preventDefault

    slideEl.addEventListener("touchend", async (e) => {
      // Only trigger on single-finger touch
      if (
        e.touches.length > 0 ||
        (e.changedTouches && e.changedTouches.length > 1)
      ) {
        return;
      }

      const now = Date.now();
      if (now - lastTap < 350) {
        e.preventDefault();
        await toggleGridSwiperView(true);
        lastTap = 0;
      } else {
        lastTap = now;
      }
    });

    slideEl.dataset.doubleTapHandlerAttached = "true";
  }

  pauseSlideshow() {
    if (this.swiper && this.swiper.autoplay?.running) {
      this.swiper.autoplay.stop();
    }
  }

  resumeSlideshow() {
    if (this.swiper) {
      this.swiper.autoplay.stop();
      setTimeout(() => {
        this.swiper.autoplay.start();
      }, 50);
    }
  }

  updateSlideshowIcon() {
    const playIcon = document.getElementById("playIcon");
    const pauseIcon = document.getElementById("pauseIcon");

    if (this.swiper?.autoplay?.running) {
      playIcon.style.display = "none";
      pauseIcon.style.display = "inline";
    } else {
      playIcon.style.display = "inline";
      pauseIcon.style.display = "none";
    }
  }

  async addNewSlide(offset = 0) {
    if (!state.album) return;

    let [globalIndex, totalImages, searchIndex] = getCurrentSlideIndex();

    if (slideState.isSearchMode) {
      globalIndex = slideState.resolveOffset(offset).globalIndex;
    } else {
      if (state.mode === "random") {
        globalIndex = Math.floor(Math.random() * totalImages);
      } else {
        globalIndex = globalIndex + offset;
        globalIndex = (globalIndex + totalImages) % totalImages;
      }
    }
    await this.addSlideByIndex(globalIndex, searchIndex);
  }

  async addSlideByIndex(
    globalIndex,
    searchIndex = null,
    prepend = false,
    notRandom = null
  ) {
    if (!this.swiper) return;

    if (
      state.mode === "random" &&
      !slideState.isSearchMode &&
      notRandom === null
    ) {
      const totalImages = slideState.totalAlbumImages;
      globalIndex = Math.floor(Math.random() * totalImages);
    }

    const exists = Array.from(this.swiper.slides).some(
      (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
    );
    if (exists) return;

    let currentScore, currentCluster, currentColor;
    if (slideState.isSearchMode && searchIndex !== null) {
      const results = slideState.searchResults[searchIndex];
      currentScore = results?.score || "";
      currentCluster = results?.cluster || "";
      currentColor = results?.color || "#000000";
    }

    try {
      const data = await fetchImageByIndex(globalIndex);

      if (!data || Object.keys(data).length === 0) {
        return;
      }

      const path = data.filepath;
      const url = data.image_url;
      const metadata_url = data.metadata_url;
      const slide = document.createElement("div");
      slide.className = "swiper-slide";

      if (this.hasTouchCapability) {
        slide.innerHTML = `
          <div class="swiper-zoom-container">
            <img src="${url}" alt="${data.filename}" />
          </div>
       `;
      } else {
        slide.innerHTML = `
          <img src="${url}" alt="${data.filename}" />
        `;
      }

      slide.dataset.filename = data.filename || "";
      slide.dataset.description = data.description || "";
      slide.dataset.filepath = path || "";
      slide.dataset.score = currentScore || "";
      slide.dataset.cluster = currentCluster || "";
      slide.dataset.color = currentColor || "#000000";
      slide.dataset.globalIndex = data.index || 0;
      slide.dataset.total = data.total || 0;
      slide.dataset.searchIndex = searchIndex !== null ? searchIndex : "";
      slide.dataset.metadata_url = metadata_url || "";
      slide.dataset.reference_images = JSON.stringify(
        data.reference_images || []
      );

      // Attach double-tap/double-click handler immediately
      this.attachDoubleTapHandler(slide);

      if (prepend) {
        this.swiper.prependSlide(slide);
      } else {
        this.swiper.appendSlide(slide);
      }
    } catch (error) {
      console.error("Failed to add new slide:", error);
      alert(`Failed to add new slide: ${error.message}`);
      return;
    }
  }

  async handleSlideChange() {
    const { globalIndex } = slideState.getCurrentSlide();
    const slideEls = this.swiper.slides;
    let activeIndex = Array.from(slideEls).findIndex(
      (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
    );
    if (activeIndex === -1) activeIndex = 0;
    const activeSlide = slideEls[activeIndex];
    if (activeSlide) {
      const globalIndex = parseInt(activeSlide.dataset.globalIndex, 10) || 0;
      const searchIndex = parseInt(activeSlide.dataset.searchIndex, 10) || 0;
      slideState.updateFromExternal(globalIndex, searchIndex);
    }
    updateMetadataOverlay(this.currentSlide());
  }

  removeSlidesAfterCurrent() {
    if (!this.swiper) return;
    const { globalIndex } = slideState.getCurrentSlide();
    const slideEls = this.swiper.slides;
    let activeIndex = Array.from(slideEls).findIndex(
      (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
    );
    if (activeIndex === -1) activeIndex = 0;
    const slidesToRemove = slideEls.length - activeIndex - 1;
    if (slidesToRemove > 0) {
      this.swiper.removeSlide(activeIndex + 1, slidesToRemove);
    }
    setTimeout(() => this.enforceHighWaterMark(), 500);
  }

  currentSlide() {
    if (!this.swiper) return null;
    return this.swiper.slides[this.swiper.activeIndex] || null;
  }

  async resetAllSlides() {
    if (!this.swiper) return;

    const slideShowRunning = this.swiper?.autoplay?.running;
    this.pauseSlideshow();

    this.swiper.removeAllSlides();

    const { globalIndex, searchIndex } = slideState.getCurrentSlide();

    const swiperContainer = document.getElementById("singleSwiper");
    if (swiperContainer) swiperContainer.style.visibility = "hidden";

    // Add previous slide if available
    const { globalIndex: prevGlobal, searchIndex: prevSearch } =
      slideState.resolveOffset(-1);
    if (prevGlobal !== null) {
      await this.addSlideByIndex(prevGlobal, prevSearch);
    }

    // Add current slide
    const previousMode = state.mode;
    if (globalIndex > 0) state.mode = "chronological";
    await this.addSlideByIndex(globalIndex, searchIndex);
    state.mode = previousMode;

    // Add next slide if available
    const { globalIndex: nextGlobal, searchIndex: nextSearch } =
      slideState.resolveOffset(1);
    if (nextGlobal !== null) {
      await this.addSlideByIndex(nextGlobal, nextSearch);
    }

    // Navigate to the current slide
    const slideIndex = prevGlobal !== null ? 1 : 0;
    this.swiper.slideTo(slideIndex, 0);

    await new Promise(requestAnimationFrame);
    if (swiperContainer) swiperContainer.style.visibility = "";

    updateMetadataOverlay(this.currentSlide());
    if (slideShowRunning) this.resumeSlideshow();

    setTimeout(() => updateCurrentImageMarker(window.umapPoints), 500);
  }

  enforceHighWaterMark(backward = false) {
    const maxSlides = state.highWaterMark || 50;
    const swiper = this.swiper;
    const slides = swiper.slides.length;

    if (slides > maxSlides) {
      let slideShowRunning = swiper.autoplay.running;
      this.pauseSlideshow();

      if (backward) {
        swiper.removeSlide(swiper.slides.length - 1);
      } else {
        swiper.removeSlide(0);
      }

      if (slideShowRunning) this.resumeSlideshow();
    }
  }

  async seekToSlideIndex(event) {
    let { globalIndex, searchIndex, totalCount, isSearchMode } = event.detail;

    if (isSearchMode) {
      globalIndex = slideState.searchToGlobal(searchIndex);
    }

    let slideEls = this.swiper.slides;
    const exists = Array.from(slideEls).some(
      (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
    );
    if (exists) {
      const targetSlideIdx = Array.from(slideEls).findIndex(
        (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
      );
      if (targetSlideIdx !== -1) {
        this.isInternalSlideChange = true;
        this.swiper.slideTo(targetSlideIdx, 300);
        this.isInternalSlideChange = false;
        updateMetadataOverlay(this.currentSlide());
        return;
      }
    }

    this.swiper.removeAllSlides();

    let origin = -2;
    const slides_to_add = 5;
    if (globalIndex + origin < 0) {
      origin = 0;
    }

    const swiperContainer = document.getElementById("singleSwiper");
    swiperContainer.style.visibility = "hidden";

    for (let i = origin; i < slides_to_add; i++) {
      if (searchIndex + i >= totalCount) break;
      if (globalIndex + i < 0) continue;
      if (globalIndex + i >= slideState.totalAlbumImages) break;
      await this.addSlideByIndex(globalIndex + i, searchIndex + i, false, true);
    }

    slideEls = this.swiper.slides;
    let targetSlideIdx = Array.from(slideEls).findIndex(
      (el) => parseInt(el.dataset.globalIndex, 10) === globalIndex
    );
    if (targetSlideIdx === -1) targetSlideIdx = 0;
    this.swiper.slideTo(targetSlideIdx, 0);

    swiperContainer.style.visibility = "visible";
    updateMetadataOverlay(this.currentSlide());
  }
}
