import sys
# Import sleep() fn so we can pause the game for a moment when a ship is hit
from time import sleep
import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to score game stats and create a scoreboard
                # Create an instance to store game statistics.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        # Create a group to store live bullets
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # Make the play button. -- create an instance
        self.play_button = Button(self, "Play")
    
    def run_game(self):
        """Start the main loop for the game."""
        while True:
            # We always need to call check events even if game is inactive (ex: user presses "Q")
            self._check_events()

            # Parts that run when game is active
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            
            self._update_screen()
                
    def _check_events(self):
        """Respond to keypresses and mouse events."""
            # Watch for keyboard and mouse events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            # Detect if player is clicking on play button
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # get mouse cursor's coordinates
                mouse_pos = pygame.mouse.get_pos()
                # send values to check play method
                self._check_play_button(mouse_pos)
    
    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        # Check to see if collide point of mouse click overlaps with play btn
        if button_clicked and not self.stats.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()
            # Reset the game statistics. to give player 3 new ships and set game to active so it starts
                # only works if button is clicked and game isn't active
            self.stats.reset_stats()
            self.stats.game_active = True
            # prep scoreboard with zero for new game
            self.sb.prep_score()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Hide the mouse cursor:
            pygame.mouse.set_visible(False)
    
    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            # Move the ship to the right.
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """Create a new bullet (instance) and add it to the bullets group (add is similar to append() but used for PyGame groups)."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update position of bullets on each pass thru loop (updates each bullet in group)
        self.bullets.update()

        # Get rid of bullets that have disappeared. Loop over a copy of the group to remove items bc can't remove items within for loop
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self._check_bullet_alien_collisions()
    
    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        
        # Check for any bullets that have hit aliens.
        # If so, get rid of the bullet and the alien.
        # The true arguments tell PyGame to delete the bullets and aliens that have collided
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        # update score when alien is shot
        if collisions:
            for aliens in collisions.values():
                # make sure to score all hits -- count all aliens hit
                self.stats.score += self.settings.alien_points * len(aliens)
            # create new image
            self.sb.prep_score()

        # Check if aliens group is empty (False)
        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()
    
    def _update_aliens(self):
        """
        Check if the fleet is at an edge,
            then update the positions of all aliens in the fleet.
        """
        self._check_fleet_edges()
        # use update method in aliens group to call each alien's update method (update positions of aliens)
        self.aliens.update()

        # Look for alien-ship collisions.
        # spritecollideany loops thru aliens group and returns first alien that collided w/the ship
            # If no collisions occur, spritecollideany() returns None and if block won't execute
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        
        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()

    # Create a new method
    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        # If the player has ships left, continue game
        if self.stats.ships_left > 0:
            # Decrement ships_left.
            self.stats.ships_left -= 1

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Pause. so player can see that they've been hit
            sleep(0.5)
            # code moves on to _update_screen() method which draws a new fleet to the screen
        # If the player has no ships left, set game_active to False
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)
    
    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                self._ship_hit()
                break
        
    def _create_fleet(self):
        """Create the fleet of aliens"""
        # Create an alien and find the number of aliens in a row.
        # Spacing between each alien is equal to one alien width.
        alien = Alien(self)
        # Size attribute contains w and h of rect obj
        alien_width, alien_height = alien.rect.size
        # figure out space needed by dividing available space by width of an alien (alien plus space next to it)
        # floor division (//) divides 2 numbers and drops any remainder
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)
        
        # Determine the number of rows of aliens that fit on the screen.
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - 
                                (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # Create the full fleet of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                # Create aliens in one row
                self._create_alien(alien_number, row_number)
    
    def _create_alien(self, alien_number, row_number):
            """Create an alien and place it in the row."""
            alien = Alien(self)
            # Width inside method to make it easier to add new rows and create an entire fleet
            alien_width, alien_height = alien.rect.size
            # Create a new alien and set its x value
            # Each alien is pushed to the right one alien width from the left margin
            # Multiply alien width * 2 to account for space ea alien takes up
            # multiply that by position in row
            alien.x = alien_width + 2 * alien_width * alien_number
            # Alien's x attribute is used to set position of rect
            alien.rect.x = alien.x
            # Set the y value by adding alien height (empty space at top of screen) with 2 alien heights below previous row
                # (alien height times two then multiply by row number)
            alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
            # Add it to the alien group
            self.aliens.add(alien)
    
    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge. -- change fleet direction"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break
    
    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        # loop thru all aliens and drop each one using fleet_drop_speed
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        # change value of fleet_direction -- vertical position
        self.settings.fleet_direction *= -1

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
         # Redraw the screen during each pass through the loop.
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        # Loop through bullets in group and draw each one
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        # Make the aliens appear
        self.aliens.draw(self.screen)

        # Draw the score info
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently drawn screen visible.
        pygame.display.flip()
            

if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()