Feature: Watch a live streamer found through search on Twitch mobile web
  As a viewer on a mobile browser
  I want to search for a game and open one of its live channels
  So that I can watch it without installing the app

  Background:
    Given I open Twitch mobile web

  @p0 @wap
  Scenario Outline: Search "<game>" and open one of its live streamers
    When I tap the search icon
    And I search for "<game>"
    And I scroll down <scrolls> times
    Then the search results include live channels playing "<game>"
    When I select a streamer playing "<game>"
    Then the streamer page is fully loaded on the mobile site
    And the selected streamer is playing "<game>"
    And I take a screenshot of the streamer page

    Examples: Task scenario
      | game         | scrolls |
      | StarCraft II | 2       |

    @extra
    Examples: Extra search case, opt-in with -m extra
      | game              | scrolls |
      | League of Legends | 2       |
