from __future__ import print_function
import sys
import os
import datetime
from xlizard.combined_metrics import CombinedMetrics
from xlizard.sourcemonitor_metrics import SourceMonitorMetrics, Config
from xlizard.sourcemonitor_metrics import FileAnalyzer, Config, CodeParser

# Duck game functions - defined inline to avoid import issues
def get_duck_game_script():
    """Returns the JavaScript code for the duck game"""
    return """
<script>
class DuckGame {
    constructor() {
        this.isActive = false;
        this.score = 0;
        this.lives = 5;
        this.ducks = [];
        this.spawnInterval = null;
        this.animationFrame = null;
        this.baseSpeed = 2;
        this.speedMultiplier = 1;
        this.gameContainer = null;
        this.scoreDisplay = null;
        this.livesDisplay = null;
        this.gameOverScreen = null;
        this.lastSpeedIncrease = 0;
        this.spawnRate = 1500;
        this.maxDucks = 7;
        this.typedChars = '';
        this.activationTimer = null;
        
        this.init();
    }

    init() {
        this.createGameUI();
        this.setupEventListeners();
    }

    createGameUI() {
        // Create game container - initially hidden
        this.gameContainer = document.createElement('div');
        this.gameContainer.id = 'duckGameContainer';
        this.gameContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10000;
            overflow: hidden;
            display: none;
        `;

        // Create score display (RIGHT TOP) - initially hidden
        this.scoreDisplay = document.createElement('div');
        this.scoreDisplay.id = 'duckGameScore';
        this.scoreDisplay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            font-size: 24px;
            font-weight: bold;
            color: #ff6b35;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            pointer-events: none;
            z-index: 10001;
            font-family: 'Inter', sans-serif;
            border: 3px solid rgba(255, 107, 53, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            display: none;
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        `;
        this.scoreDisplay.textContent = 'Score: 0';

        // Create lives display (LEFT TOP) - initially hidden
        this.livesDisplay = document.createElement('div');
        this.livesDisplay.id = 'duckGameLives';
        this.livesDisplay.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            font-size: 24px;
            color: #ff6b35;
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 12px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
            pointer-events: none;
            z-index: 10001;
            font-family: 'Inter', sans-serif;
            border: 3px solid rgba(255, 107, 53, 0.3);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            display: none;
            opacity: 0;
            transform: translateY(-20px);
            transition: opacity 0.5s ease, transform 0.5s ease;
        `;
        this.updateLivesDisplay();

        // Create game over screen
        this.gameOverScreen = document.createElement('div');
        this.gameOverScreen.id = 'duckGameOver';
        this.gameOverScreen.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.98);
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            text-align: center;
            z-index: 10002;
            pointer-events: auto;
            display: none;
            font-family: 'Inter', sans-serif;
            min-width: 350px;
            border: 4px solid rgba(255, 107, 53, 0.5);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
        `;
        this.gameOverScreen.innerHTML = `
            <h2 style="color: #ff6b35; margin-bottom: 25px; font-size: 32px;">Game Over!</h2>
            <p style="font-size: 20px; margin-bottom: 15px; color: #333;">Final Score: <span id="finalScore" style="font-weight: bold; color: #ff6b35;">0</span></p>
            <div style="display: flex; gap: 20px; justify-content: center; margin-top: 30px;">
                <button id="restartGame" style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 18px;
                    font-weight: bold;
                    box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
                    transition: all 0.3s ease;
                ">Restart</button>
                <button id="closeGame" style="
                    background: linear-gradient(135deg, #ff6b35 0%, #ff8e53 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 18px;
                    font-weight: bold;
                    box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
                    transition: all 0.3s ease;
                ">Work</button>
            </div>
        `;

        document.body.appendChild(this.gameContainer);
        document.body.appendChild(this.scoreDisplay);
        document.body.appendChild(this.livesDisplay);
        document.body.appendChild(this.gameOverScreen);

        // Add game over event listeners
        document.getElementById('restartGame').addEventListener('click', () => this.restartGame());
        document.getElementById('closeGame').addEventListener('click', () => this.stopGame());
        
        // Add hover effects
        const restartBtn = document.getElementById('restartGame');
        const closeBtn = document.getElementById('closeGame');
        
        restartBtn.addEventListener('mouseenter', () => {
            restartBtn.style.transform = 'translateY(-3px)';
            restartBtn.style.boxShadow = '0 6px 20px rgba(79, 172, 254, 0.6)';
        });
        restartBtn.addEventListener('mouseleave', () => {
            restartBtn.style.transform = 'translateY(0)';
            restartBtn.style.boxShadow = '0 4px 15px rgba(79, 172, 254, 0.4)';
        });
        
        closeBtn.addEventListener('mouseenter', () => {
            closeBtn.style.transform = 'translateY(-3px)';
            closeBtn.style.boxShadow = '0 6px 20px rgba(255, 107, 53, 0.6)';
        });
        closeBtn.addEventListener('mouseleave', () => {
            closeBtn.style.transform = 'translateY(0)';
            closeBtn.style.boxShadow = '0 4px 15px rgba(255, 107, 53, 0.4)';
        });
    }

    setupEventListeners() {
        // Listen for keyboard input
        document.addEventListener('keydown', (e) => {
            if (this.isActive) return;
            
            this.typedChars += e.key.toLowerCase();
            
            // Keep only last 10 characters
            if (this.typedChars.length > 10) {
                this.typedChars = this.typedChars.slice(-10);
            }
            
            // Check if "duck" is typed
            if (this.typedChars.includes('duck')) {
                if (this.activationTimer) {
                    clearTimeout(this.activationTimer);
                }
                
                this.activationTimer = setTimeout(() => {
                    if (!this.isActive) {
                        this.startGame();
                    }
                }, 300);
            }
        });

        // Listen for clicks on ducks
        this.gameContainer.addEventListener('click', (e) => {
            if (this.isActive && e.target.classList.contains('duck')) {
                this.hitDuck(e.target);
            }
        });
    }

    startGame() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.score = 0;
        this.lives = 5;
        this.ducks = [];
        this.baseSpeed = 2;
        this.speedMultiplier = 1;
        this.lastSpeedIncrease = Date.now();
        this.spawnRate = 1500;
        this.typedChars = '';
        
        this.scoreDisplay.textContent = 'Score: 0';
        this.updateLivesDisplay();
        this.gameOverScreen.style.display = 'none';
        
        this.showGameUI();
        this.startSpawning();
        this.gameLoop();
        
        console.log('🦆 Duck Game Started!');
    }

    stopGame() {
        this.isActive = false;
        this.clearGame();
        this.hideGameUI();
        console.log('🦆 Duck Game Stopped');
    }

    restartGame() {
        this.stopGame();
        setTimeout(() => this.startGame(), 100);
    }

    clearGame() {
        if (this.spawnInterval) {
            clearInterval(this.spawnInterval);
            this.spawnInterval = null;
        }
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        // Remove all ducks
        this.ducks.forEach(duck => {
            if (duck.element && duck.element.parentNode) {
                duck.element.remove();
            }
        });
        this.ducks = [];
    }

    hideGameUI() {
        // Hide game container
        this.gameContainer.style.display = 'none';
        
        // Hide and reset UI elements with animation
        this.scoreDisplay.style.display = 'none';
        this.scoreDisplay.style.opacity = '0';
        this.scoreDisplay.style.transform = 'translateY(-20px)';
        
        this.livesDisplay.style.display = 'none';
        this.livesDisplay.style.opacity = '0';
        this.livesDisplay.style.transform = 'translateY(-20px)';
        
        this.gameOverScreen.style.display = 'none';
    }

    showGameUI() {
        // Show game container
        this.gameContainer.style.display = 'block';
        
        // Show score and lives with smooth animation
        setTimeout(() => {
            this.scoreDisplay.style.display = 'block';
            this.livesDisplay.style.display = 'block';
            
            // Trigger animation
            setTimeout(() => {
                this.scoreDisplay.style.opacity = '1';
                this.scoreDisplay.style.transform = 'translateY(0)';
                this.livesDisplay.style.opacity = '1';
                this.livesDisplay.style.transform = 'translateY(0)';
            }, 50);
        }, 100);
    }

    startSpawning() {
        this.lastSpeedIncrease = Date.now();
        
        this.spawnInterval = setInterval(() => {
            if (this.ducks.length < this.maxDucks) {
                this.spawnDuck();
            }
        }, this.spawnRate);
    }

    spawnDuck() {
        const duck = document.createElement('div');
        duck.className = 'duck';
        duck.style.cssText = `
            position: absolute;
            width: 60px;
            height: 60px;
            background-image: url("data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/Pgo8c3ZnIGhlaWdodD0iNjAiIHdpZHRoPSI2MCIgdmlld0JveD0iMCAwIDUxMiA1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxnPgoJPHBhdGggZmlsbD0iI0QxODc3MCIgZD0iTTkwLjQ2NSwxODYuOTEyYzAuMDg2LTcuNTgxLTUuMjYtMjcuNDksMi43NzEtNDMuNzgxYzguMDI1LTE2LjI5MS00Mi4yMjYtMjAuNTQ2LTY3LjY4MiwwLjM2NwoJCWMtMjQuNTEsMjAuMTM3LDEuNzY0LDM3LjQ2OCwxNy45MzgsMzMuNjU3Qzc2LjI2NywxNjkuNDI4LDkwLjI5OSwyMDIuMjYxLDkwLjQ2NSwxODYuOTEyeiIvPgoJPHBhdGggZmlsbD0iI0REODk2OCIgZD0iTTczLjMxNSw5Ni4wMDljMC4wNzksNy41NzQtNS4yNiwyNy40ODMsMi43NjQsNDMuNzgyYzguMDI1LDE2LjI3Ny00Ni43OTksMjUuMTA1LTY3LjY3NC0wLjM3NQoJCWMtMjAuODc4LTI1LjQ4LDEuNzYtMzcuNDYxLDE3Ljk0MS0zMy42NUM1OS4xMDIsMTEzLjQ4NSw3My4xMzcsODAuNjU0LDczLjMxNSw5Ni4wMDl6Ii8+Cgk8cGF0aCBmaWxsPSIjRjZFMTc0IiBkPSJNNzYuNDUsMjY0LjIxMWMxOC4xODMtMjEuNDA2LDMzLjA5Mi0zMS4wMzgsMjAuODIxLTUwLjQzMwoJCWMtMjMuNDAyLTIzLjQwOC0zNC4zMDktNDguNzQzLTM0LjMwOS04NC40NThjMC0zNS43MDksMTQuNDc2LTY4LjAzNSwzNy44NzYtOTEuNDM2QzEyNC4yNDMsMTQuNDgzLDE1Ni41NjMsMCwxOTIuMjc4LDAKCQlzNjguMDM1LDE4LjQ4Myw5MS40NDMsMzcuODg0YzIzLjQwMSwyMy40MDIsMzcuODcsNTUuNzI4LDM3Ljg3LDkxLjQzNmMwLDUyLjc4OS00Mi4yMjIsOTUuMDExLTQyLjIyMiwxMjEuNAoJCWMtMi42NCwxMC41NjEsMTUuODM1LDIzLjc2MSwzOS41ODIsMjMuNzYxYzIzLjc2MSwwLDEwMi45MzIsMTguNDY3LDE2MC45ODgtNTguMDYzYzE1LjI4LTIxLjEyMiwzMy43NTUtOS4yMzgsMzEuNjc1LDIxLjEwNwoJCUM1MDkuNjE4LDI2Ni42MDksNDkzLjEzMyw1MTIsMzE4Ljk1MSw1MTJjLTUwLjEzNSwwLTQzLjc4OCwwLTEzOS44NzQsMGMtNDAuMDc0LDAtNzYuMzYtMTYuMjUtMTAyLjYyNy00Mi41MTMKCQljLTI2LjI3My0yNi4yNy00Mi41Mi02Mi41NTQtNDIuNTItMTA2LjY0OUMzMy45MywzMjYuNzY1LDUwLjE3NiwyOTAuNDc0LDc2LjQ1LDI2NC4yMTEiLz4KCTxwYXRoIGZpbGw9IiVFNUQyOUIiIGQ9Ik0yMTkuNTMzLDM0MC40NThoMTkzLjIxNmMyMS4xMDgsMCwyNi4zODgsMzYuOTQxLTcuOTIsNTguMDYzYzAsMjYuMzgtMTMuMjAxLDY1Ljk3LTUyLjc4Miw2NS45NwoJCWMtMzkuNTk2LDAtODcuMDkyLDAtMTIxLjQsMGMtMzQuMzE2LDAtNTguMDY0LTM5LjU5LTU4LjA2NC02My4zMzdDMTcyLjU4NCwzNzcuMzk5LDE5NS43NzcsMzQwLjQ1OCwyMTkuNTMzLDM0MC40NTh6Ii8+Cgk8cGF0aCBmaWxsPSIjRjBENzgwIiBkPSJNMjA2LjMzMSwzMjQuNjE2aDE5My4yMThjMjEuMTA4LDAsMjYuMzg4LDM2Ljk0OS03LjkyLDU4LjA2NGMwLDI2LjM5NS0xMy4xOTQsNjUuOTgzLTUyLjc3Niw2NS45ODMKCQljLTM5LjU4OSwwLTg3LjA5NywwLTEyMS40MDYsMHMtNTguMDU3LTM5LjU4OS01OC4wNTctNjMuMzQ0QzE1OS4zOSwzNjEuNTY1LDE4Mi41ODMsMzI0LjYxNiwyMDYuMzMxLDMyNC42MTZ6Ii8+Cgk8cGF0aCBmaWxsPSIjRkZGRkZGIiBkPSJNMTU5LjM5LDEwOS41MjJjMCwxNi43Ny0xMy41OTYsMzAuMzU5LTMwLjM0OCwzMC4zNTljLTE2Ljc2MywwLTMwLjM1NS0xMy41ODktMzAuMzU1LTMwLjM1OQoJCWMwLTE2Ljc0OCwxMy41OTItMzAuMzQ0LDMwLjM1NS0zMC4zNDRDMTQ1Ljc5NCw3OS4xNzcsMTU5LjM5LDkyLjc3MywxNTkuMzksMTA5LjUyMnoiLz4KCTxwYXRoIGZpbGw9IiM2NDYzNjMiIGQ9Ik0xNDMuNTU2LDEwOS41MjJjMCw4LjAyNS02LjUwMywxNC41MjUtMTQuNTE0LDE0LjUyNWMtOC4wMTgsMC0xNC41MTgtNi41LTE0LjUxOC0xNC41MjUKCQljMC04LjAwMyw2LjUtMTQuNTAzLDE0LjUxOC0xNC41MDNDMTM3LjA1Miw5NS4wMTgsMTQ3LjU1NiwxMDEuNTE4LDE0My41NTYsMTA5LjUyMnoiLz4KPC9nPgo8L3N2Zz4K");
            background-size: contain;
            background-repeat: no-repeat;
            pointer-events: auto;
            cursor: crosshair;
            top: -70px;
            left: ${Math.random() * (window.innerWidth - 80)}px;
            transition: transform 0.2s ease, opacity 0.2s ease;
            z-index: 10001;
            filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.3));
        `;

        this.gameContainer.appendChild(duck);

        const duckObj = {
            element: duck,
            speed: this.baseSpeed * this.speedMultiplier,
            x: parseInt(duck.style.left),
            y: -70,
            isHit: false
        };

        this.ducks.push(duckObj);
    }

    gameLoop() {
        if (!this.isActive) return;

        const currentTime = Date.now();
        
        // Increase difficulty every 5 seconds
        if (currentTime - this.lastSpeedIncrease > 5000) {
            this.speedMultiplier = Math.min(this.speedMultiplier + 0.2, 4);
            this.spawnRate = Math.max(this.spawnRate - 100, 600);
            this.lastSpeedIncrease = currentTime;
        }

        // Update ducks
        for (let i = this.ducks.length - 1; i >= 0; i--) {
            const duck = this.ducks[i];
            if (duck.isHit) continue;

            duck.y += duck.speed;
            duck.element.style.top = duck.y + 'px';

            // Check if duck is out of bounds
            if (duck.y > window.innerHeight) {
                this.missDuck(i);
            }
        }

        this.animationFrame = requestAnimationFrame(() => this.gameLoop());
    }

    hitDuck(duckElement) {
        const duckIndex = this.ducks.findIndex(d => d.element === duckElement);
        if (duckIndex === -1 || this.ducks[duckIndex].isHit) return;

        const duck = this.ducks[duckIndex];
        duck.isHit = true;

        // Add hit effect
        duck.element.style.transform = 'scale(1.3) rotate(15deg)';
        duck.element.style.opacity = '0.5';
        duck.element.style.filter = 'brightness(2) drop-shadow(0 0 8px #ff6b35)';
        
        setTimeout(() => {
            if (duck.element && duck.element.parentNode) {
                duck.element.remove();
            }
            this.ducks.splice(duckIndex, 1);
        }, 150);

        this.score += 10;
        this.scoreDisplay.textContent = `Score: ${this.score}`;
        this.scoreDisplay.style.animation = 'none';
        setTimeout(() => {
            this.scoreDisplay.style.animation = 'scorePop 0.3s ease';
        }, 10);
    }

    missDuck(duckIndex) {
        const duck = this.ducks[duckIndex];
        if (duck.element && duck.element.parentNode) {
            duck.element.remove();
        }
        this.ducks.splice(duckIndex, 1);

        this.lives--;
        this.updateLivesDisplay();

        this.livesDisplay.style.animation = 'none';
        setTimeout(() => {
            this.livesDisplay.style.animation = 'lifeLost 0.5s ease';
        }, 10);

        if (this.lives <= 0) {
            this.gameOver();
        }
    }

    updateLivesDisplay() {
        const hearts = '❤️'.repeat(this.lives) + '♡'.repeat(5 - this.lives);
        this.livesDisplay.innerHTML = `Lives: <span style="font-size: 26px;">${hearts}</span>`;
    }

    gameOver() {
        this.isActive = false;
        this.clearGame();
        
        document.getElementById('finalScore').textContent = this.score;
        this.gameOverScreen.style.display = 'block';
    }
}

// Initialize game when page loads
let duckGame;
document.addEventListener('DOMContentLoaded', () => {
    duckGame = new DuckGame();
});

window.DuckGame = DuckGame;
</script>
"""

def get_duck_game_css():
    """Returns CSS styles for the duck game"""
    return """
<style>
.duck {
    animation: duckFloat 0.8s ease-in-out infinite alternate;
}

@keyframes duckFloat {
    0% { transform: translateY(0px) rotate(-2deg); }
    100% { transform: translateY(-8px) rotate(2deg); }
}

.duck:hover {
    filter: drop-shadow(2px 2px 6px rgba(255, 107, 53, 0.8)) brightness(1.1) !important;
    transform: scale(1.05) !important;
}

#duckGameContainer {
    user-select: none;
    -webkit-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
}

@keyframes scorePop {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

@keyframes lifeLost {
    0% { transform: translateX(0); }
    25% { transform: translateX(-10px); }
    50% { transform: translateX(10px); }
    75% { transform: translateX(-5px); }
    100% { transform: translateX(0); }
}

#duckGameOver {
    animation: modalAppear 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes modalAppear {
    from { 
        opacity: 0; 
        transform: translate(-50%, -50%) scale(0.7); 
    }
    to { 
        opacity: 1; 
        transform: translate(-50%, -50%) scale(1); 
    }
}

/* Responsive design */
@media (max-width: 768px) {
    #duckGameScore, #duckGameLives {
        font-size: 18px !important;
        padding: 8px 16px !important;
        top: 10px !important;
    }
    
    #duckGameLives {
        left: 10px !important;
    }
    
    #duckGameScore {
        right: 10px !important;
    }
    
    .duck {
        width: 50px !important;
        height: 50px !important;
    }
    
    #duckGameOver {
        min-width: 280px !important;
        padding: 30px !important;
    }
}
</style>
"""

def html_output(result, options, *_):
    try:
        from jinja2 import Template
    except ImportError:
        sys.stderr.write(
                "HTML Output depends on jinja2. `pip install jinja2` first")
        sys.exit(2)

    # Get SourceMonitor metrics (file or directory)
    try:
        sm = SourceMonitorMetrics(options.paths[0] if options.paths else '.')
        sm.analyze_directory(exit_on_error=False)

        sm_metrics = {}
        for m in sm.get_metrics():
            original_path = m['file_path']
            normalized_path = os.path.normpath(original_path)
            basename = os.path.basename(normalized_path)
            abs_path = os.path.normpath(
                os.path.join(os.path.dirname(sm.path), original_path)
                if not os.path.isabs(original_path) else original_path
            )

            sm_metrics[normalized_path] = m
            sm_metrics[basename] = m
            sm_metrics[f"./{normalized_path}"] = m
            sm_metrics[normalized_path.replace('\\', '/')] = m
            sm_metrics[abs_path] = m
            sm_metrics[os.path.abspath(original_path)] = m

    except Exception as e:
        sys.stderr.write(f"Warning: SourceMonitor metrics not available ({str(e)})\n")
        sm_metrics = {}

    file_list = []
    for source_file in result:
        if source_file and not source_file.filename.endswith('.h'):
            file_key = os.path.normpath(source_file.filename)
            file_metrics = sm_metrics.get(file_key) or sm_metrics.get(os.path.basename(file_key))

            combined = CombinedMetrics(
                source_file,
                file_metrics
            )
            
            dirname = combined.dirname
            source_file_dict = {
                "filename": combined.filename,
                "basename": combined.basename,
                "dirname": dirname,
                "comment_percentage": combined.comment_percentage,
                "max_block_depth": combined.max_block_depth,
                "pointer_operations": combined.pointer_operations,
                "preprocessor_directives": combined.preprocessor_directives,
                "logical_operators": combined.logical_operators,
                "conditional_statements": combined.conditional_statements,
                "lines_of_code": combined.lines_of_code,
                "comment_lines": combined.comment_lines,
                "total_lines": combined.total_lines,
                "sourcemonitor": file_metrics
            }
            
            func_list = []
            max_complexity = 0
            for source_function in combined.functions:
                if source_function:
                    try:
                        func_dict = _create_dict(source_function, source_file.filename)
                        if func_dict:
                            func_dict['in_disable_block'] = _is_in_disable_block(
                                source_file.filename, 
                                source_function.start_line, 
                                source_function.end_line
                            )
                            if not hasattr(source_function, 'token_count') or func_dict.get('token_count') is None:
                                func_dict['token_count'] = 0
                            func_list.append(func_dict)
                            if not func_dict['in_disable_block'] and func_dict.get('cyclomatic_complexity', 0) > max_complexity:
                                max_complexity = func_dict['cyclomatic_complexity']
                    except Exception as e:
                        print(f"Warning: Skipping function {source_function.name} due to error: {str(e)}")
                        problem_func = {
                            'name': source_function.name,
                            'cyclomatic_complexity': getattr(source_function, 'cyclomatic_complexity', 0),
                            'nloc': getattr(source_function, 'nloc', 0),
                            'token_count': getattr(source_function, 'token_count', 0),
                            'parameter_count': getattr(source_function, 'parameter_count', 0),
                            'length': int(getattr(source_function, 'length', 0) or 0),
                            'start_line': getattr(source_function, 'start_line', 0),
                            'end_line': getattr(source_function, 'end_line', 0),
                            'max_depth': 0,
                            'has_complex_preprocessor': True,
                            'balanced_blocks': False,
                            'in_disable_block': False
                        }
                        func_list.append(problem_func)
                        continue
            
            source_file_dict["functions"] = func_list
            source_file_dict["max_complexity"] = max_complexity
            
            active_functions = [f for f in func_list if not f.get('in_disable_block', False)]
            if active_functions:
                source_file_dict["avg_complexity"] = sum(
                    func.get('cyclomatic_complexity', 0) for func in active_functions
                ) / len(active_functions)
            else:
                source_file_dict["avg_complexity"] = 0
            
            source_file_dict["active_functions_count"] = len([f for f in func_list if not f.get('in_disable_block', False)])
            source_file_dict["disabled_functions_count"] = len([f for f in func_list if f.get('in_disable_block', False)])
            source_file_dict["problem_functions"] = len([f for f in active_functions if f.get('cyclomatic_complexity', 0) > options.thresholds['cyclomatic_complexity']])
            
            file_list.append(source_file_dict)
    
    # Group files by directories
    dir_groups = {}
    for file in file_list:
        dirname = file['dirname']
        if dirname not in dir_groups:
            dir_groups[dirname] = []
        dir_groups[dirname].append(file)
    
    # Calculate metrics for dashboard (only active functions)
    complexity_data = []
    comment_data = []
    depth_data = []
    pointer_data = []
    directives_data = []
    logical_ops_data = []
    conditional_data = []
    
    for file in file_list:
        active_functions = [f for f in file['functions'] if not f.get('in_disable_block', False)]
        if active_functions:
            complexity_data.extend([f.get('cyclomatic_complexity', 0) for f in active_functions])
        if file['comment_percentage'] is not None:
            comment_data.append(file['comment_percentage'])
        if file['max_block_depth'] is not None:
            depth_data.append(file['max_block_depth'])
        if file['pointer_operations'] is not None:
            pointer_data.append(file['pointer_operations'])
        if file['preprocessor_directives'] is not None:
            directives_data.append(file['preprocessor_directives'])
        if file['logical_operators'] is not None:
            logical_ops_data.append(file['logical_operators'])
        if file['conditional_statements'] is not None:
            conditional_data.append(file['conditional_statements'])
    
    # Prepare comment distribution data
    comment_ranges = {
        '0-10': sum(1 for p in comment_data if p <= 10),
        '10-20': sum(1 for p in comment_data if 10 < p <= 20),
        '20-30': sum(1 for p in comment_data if 20 < p <= 30),
        '30-40': sum(1 for p in comment_data if 30 < p <= 40),
        '40-50': sum(1 for p in comment_data if 40 < p <= 50),
        '50+': sum(1 for p in comment_data if p > 50)
    }
    
    # Prepare depth vs pointers data
    depth_pointers_data = []
    for f in file_list:
        if f['pointer_operations'] is not None and f['max_block_depth'] is not None:
            depth_pointers_data.append({
                'x': f['pointer_operations'], 
                'y': f['max_block_depth'], 
                'file': f['basename']
            })
    
    # Prepare complexity vs nloc data (only active functions)
    complexity_nloc_data = []
    top_complex_functions = []
    
    for file in file_list:
        for func in file['functions']:
            if not func.get('in_disable_block', False):
                nloc = func.get('nloc', 0)
                complexity = func.get('cyclomatic_complexity', 0)
                if nloc is not None and complexity is not None:
                    complexity_nloc_data.append({
                        'x': nloc,
                        'y': complexity,
                        'function': func.get('name', 'unknown'),
                        'file': file['basename']
                    })
                    
                    top_complex_functions.append({
                        'name': func.get('name', 'unknown'),
                        'complexity': complexity,
                        'nloc': nloc,
                        'file': file['basename'],
                        'filepath': file['filename']
                    })
    
    # Get top 5 most complex functions (only active)
    top_complex_functions.sort(key=lambda x: -x['complexity'])
    top_complex_functions = top_complex_functions[:5]
    
    # Get files with min/max comments
    files_with_comments = [f for f in file_list if f['comment_percentage'] is not None]
    if files_with_comments:
        files_sorted_by_comments = sorted(files_with_comments, key=lambda x: x['comment_percentage'])
        min_comments_files = files_sorted_by_comments[:5]
        max_comments_files = files_sorted_by_comments[-5:]
        max_comments_files.reverse()
    else:
        min_comments_files = []
        max_comments_files = []
    
    # Calculate code/comment/empty ratio
    total_code_lines = sum(f['lines_of_code'] for f in file_list if f['lines_of_code'] is not None)
    total_comment_lines = sum(f['comment_lines'] for f in file_list if f['comment_lines'] is not None)
    total_empty_lines = sum(f['total_lines'] - f['lines_of_code'] - f['comment_lines'] for f in file_list if all(x is not None for x in [f['total_lines'], f['lines_of_code'], f['comment_lines']]))
    
    code_ratio = {
        'code': total_code_lines,
        'comments': total_comment_lines,
        'empty': total_empty_lines
    }
    
    # Calculate directory complexity stats (only active functions)
    dir_complexity_stats = []
    for dirname, files in dir_groups.items():
        files_with_complexity = [f for f in files if f['avg_complexity'] is not None]
        if files_with_complexity:
            total_complexity = sum(f['avg_complexity'] for f in files_with_complexity)
            total_files = len(files_with_complexity)
            avg_complexity = total_complexity / total_files if total_files else 0
            dir_complexity_stats.append({
                'name': dirname,
                'avg_complexity': avg_complexity,
                'file_count': total_files
            })
    
    # Sort directories by complexity
    dir_complexity_stats.sort(key=lambda x: -x['avg_complexity'])
    
    # Update file metrics to exclude disabled functions
    total_complexity = 0
    total_functions = 0
    total_disabled_functions = 0
    problem_files = 0
    total_comments = 0
    total_depth = 0
    total_pointers = 0
    total_directives = 0
    total_logical_ops = 0
    total_conditionals = 0
    
    directory_stats = []
    
    for dirname, files in dir_groups.items():
        dir_complexity = 0
        dir_max_complexity = 0
        dir_functions = 0
        dir_disabled_functions = 0
        dir_problem_functions = 0
        dir_comments = 0
        dir_depth = 0
        dir_pointers = 0
        dir_directives = 0
        dir_logical_ops = 0
        dir_conditionals = 0
        valid_files = 0
        
        for file in files:
            active_functions = [f for f in file['functions'] if not f.get('in_disable_block', False)]
            disabled_functions = [f for f in file['functions'] if f.get('in_disable_block', False)]
            
            file['disabled_functions_count'] = len(disabled_functions)
            file['active_functions_count'] = len(active_functions)
            
            if file['avg_complexity'] is not None:
                dir_complexity += file['avg_complexity']
                valid_files += 1
            
            if file['max_complexity'] is not None:
                dir_max_complexity = max(dir_max_complexity, file['max_complexity'])
            
            dir_functions += file['active_functions_count']
            dir_disabled_functions += file['disabled_functions_count']
            dir_problem_functions += file.get('problem_functions', 0)
            
            if file['comment_percentage'] is not None:
                dir_comments += file['comment_percentage']
            if file['max_block_depth'] is not None:
                dir_depth += file['max_block_depth']
            if file['pointer_operations'] is not None:
                dir_pointers += file['pointer_operations']
            if file['preprocessor_directives'] is not None:
                dir_directives += file['preprocessor_directives']
            if file['logical_operators'] is not None:
                dir_logical_ops += file['logical_operators']
            if file['conditional_statements'] is not None:
                dir_conditionals += file['conditional_statements']
            
            total_complexity += file['avg_complexity'] if file['avg_complexity'] is not None else 0
            total_functions += file['active_functions_count']
            total_disabled_functions += file['disabled_functions_count']
            total_comments += file['comment_percentage'] if file['comment_percentage'] is not None else 0
            total_depth += file['max_block_depth'] if file['max_block_depth'] is not None else 0
            total_pointers += file['pointer_operations'] if file['pointer_operations'] is not None else 0
            total_directives += file['preprocessor_directives'] if file['preprocessor_directives'] is not None else 0
            total_logical_ops += file['logical_operators'] if file['logical_operators'] is not None else 0
            total_conditionals += file['conditional_statements'] if file['conditional_statements'] is not None else 0
            
            if file['max_complexity'] is not None and file['max_complexity'] > options.thresholds['cyclomatic_complexity']:
                problem_files += 1
        
        directory_stats.append({
            'name': dirname,
            'max_complexity': dir_max_complexity,
            'avg_complexity': dir_complexity / valid_files if valid_files else 0,
            'total_functions': dir_functions,
            'disabled_functions': dir_disabled_functions,
            'problem_functions': dir_problem_functions,
            'file_count': len(files),
            'avg_comments': dir_comments / len(files) if files and dir_comments > 0 else 0,
            'avg_depth': dir_depth / len(files) if files and dir_depth > 0 else 0,
            'avg_pointers': dir_pointers / len(files) if files and dir_pointers > 0 else 0,
            'avg_directives': dir_directives / len(files) if files and dir_directives > 0 else 0,
            'avg_logical_ops': dir_logical_ops / len(files) if files and dir_logical_ops > 0 else 0,
            'avg_conditionals': dir_conditionals / len(files) if files and dir_conditionals > 0 else 0
        })
    
    # Calculate averages safely
    valid_files_for_avg = [f for f in file_list if f['avg_complexity'] is not None]
    avg_complexity = sum(f['avg_complexity'] for f in valid_files_for_avg) / len(valid_files_for_avg) if valid_files_for_avg else 0
    
    valid_comments = [f for f in file_list if f['comment_percentage'] is not None]
    avg_comments = sum(f['comment_percentage'] for f in valid_comments) / len(valid_comments) if valid_comments else 0
    
    valid_depth = [f for f in file_list if f['max_block_depth'] is not None]
    avg_depth = sum(f['max_block_depth'] for f in valid_depth) / len(valid_depth) if valid_depth else 0
    
    valid_pointers = [f for f in file_list if f['pointer_operations'] is not None]
    avg_pointers = sum(f['pointer_operations'] for f in valid_pointers) / len(valid_pointers) if valid_pointers else 0
    
    valid_directives = [f for f in file_list if f['preprocessor_directives'] is not None]
    avg_directives = sum(f['preprocessor_directives'] for f in valid_directives) / len(valid_directives) if valid_directives else 0
    
    valid_logical_ops = [f for f in file_list if f['logical_operators'] is not None]
    avg_logical_ops = sum(f['logical_operators'] for f in valid_logical_ops) / len(valid_logical_ops) if valid_logical_ops else 0
    
    valid_conditionals = [f for f in file_list if f['conditional_statements'] is not None]
    avg_conditionals = sum(f['conditional_statements'] for f in valid_conditionals) / len(valid_conditionals) if valid_conditionals else 0
    
    # Combine thresholds with new values
    full_thresholds = {
        'cyclomatic_complexity': 15,
        'cognitive_complexity': 25,
        'nloc': 80,
        'comment_percentage': 0,
        'max_block_depth': 5,
        'pointer_operations': 100,
        'preprocessor_directives': 40,
        'logical_operators': Config.THRESHOLDS.get('logical_operators', 50),
        'conditional_statements': Config.THRESHOLDS.get('conditional_statements', 50),
        'parameter_count': 5,
        'function_count': 40,
        'token_count': 500,
        'max_nesting_depth': 5,
        'length': 150,
        'goto_count': 0,
        'return_count': 1,
        'path_count': 80,
        'calls': 7,
        'calling': 5,
    }
    full_thresholds.update(Config.THRESHOLDS)
    full_thresholds.update(getattr(options, 'file_thresholds', None) or {})
    full_thresholds.update(getattr(options, 'thresholds', {}) or {})

    from xlizard.thresholds import DEFAULT_SOFT_PCT
    from xlizard.quality_score import compute_quality_score, normalize_quality_weights
    soft_pcts = dict(DEFAULT_SOFT_PCT)
    soft_pcts.update(getattr(options, 'file_soft_pcts', None) or {})
    his_metrics = bool(getattr(options, 'his_metrics', False))
    quality_weights = normalize_quality_weights(
        getattr(options, 'quality_score_weights', None)
    )
    quality = compute_quality_score(
        file_list,
        full_thresholds,
        soft_pcts,
        his_enabled=his_metrics,
        weights=quality_weights,
    )
    
    # Prepare dashboard data
    dashboard_data = {
        'complexity_distribution': {
            'low': sum(1 for c in complexity_data if c <= full_thresholds['cyclomatic_complexity'] * 0.5),
            'medium': sum(1 for c in complexity_data if full_thresholds['cyclomatic_complexity'] * 0.5 < c <= full_thresholds['cyclomatic_complexity']),
            'high': sum(1 for c in complexity_data if c > full_thresholds['cyclomatic_complexity'])
        },
        'avg_metrics': {
            'complexity': sum(complexity_data)/len(complexity_data) if complexity_data else 0,
            'comments': sum(comment_data)/len(comment_data) if comment_data else 0,
            'depth': sum(depth_data)/len(depth_data) if depth_data else 0,
            'pointers': sum(pointer_data)/len(pointer_data) if pointer_data else 0,
            'directives': sum(directives_data)/len(directives_data) if directives_data else 0,
            'logical_ops': sum(logical_ops_data)/len(logical_ops_data) if logical_ops_data else 0,
            'conditionals': sum(conditional_data)/len(conditional_data) if conditional_data else 0
        },
        'comment_ranges': comment_ranges,
        'depth_pointers_data': depth_pointers_data,
        'complexity_nloc_data': complexity_nloc_data,
        'thresholds': full_thresholds
    }
    
    # Add duck game to template
    template_with_game = TEMPLATE.replace(
        '</style>', 
        get_duck_game_css() + '</style>'
    ).replace(
        '</body>', 
        get_duck_game_script() + '</body>'
    )
    
    output = Template(template_with_game).render(
            title='Отчёт xLizard',
            date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
            thresholds=full_thresholds, 
            dir_groups=dir_groups,
            total_files=len(file_list),
            problem_files=problem_files,
            avg_complexity=round(avg_complexity, 2),
            avg_comments=round(avg_comments, 2),
            avg_depth=round(avg_depth, 2),
            avg_pointers=round(avg_pointers, 2),
            avg_directives=round(avg_directives, 2),
            avg_logical_ops=round(avg_logical_ops, 2),
            avg_conditionals=round(avg_conditionals, 2),
            total_functions=total_functions,
            total_disabled_functions=total_disabled_functions,
            directory_stats=sorted(directory_stats, key=lambda x: -x['max_complexity']),
            dashboard_data=dashboard_data,
            top_complex_functions=top_complex_functions,
            min_comments_files=min_comments_files,
            max_comments_files=max_comments_files,
            code_ratio=code_ratio,
            dir_complexity_stats=dir_complexity_stats,
            quality=quality,
            soft_pcts=soft_pcts,
            his_metrics=his_metrics)
    print(output)
    return 0

def _get_function_code(file_path, start_line, end_line):
    """Чтение кода функции с поддержкой разных кодировок"""
    try:
        encodings = ['utf-8', 'cp1251', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    lines = f.readlines()
                    return ''.join(lines[start_line-1:end_line])
            except UnicodeDecodeError:
                continue
        
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            content = binary_content.decode('utf-8', errors='ignore')
            lines = content.split('\n')
            return '\n'.join(lines[start_line-1:end_line])
            
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return ""
    
def _create_dict(source_function, file_path):
    try:
        func_dict = {
            'name': source_function.name,
            'cyclomatic_complexity': getattr(source_function, 'cyclomatic_complexity', 0),
            'cognitive_complexity': int(
                getattr(source_function, 'cognitive_complexity', 0) or 0),
            'max_nesting_depth': int(
                getattr(source_function, 'max_nesting_depth', 0) or 0),
            'nloc': getattr(source_function, 'nloc', 0),
            'token_count': getattr(source_function, 'token_count', 0),
            'parameter_count': getattr(source_function, 'parameter_count', 0),
            'start_line': getattr(source_function, 'start_line', 0),
            'end_line': getattr(source_function, 'end_line', 0),
            'length': int(getattr(source_function, 'length', 0) or 0),
            'goto_count': int(getattr(source_function, 'goto_count', 0) or 0),
            'return_count': int(getattr(source_function, 'return_count', 0) or 0),
            'path_count': int(getattr(source_function, 'path_count', 1) or 1),
            'calls': int(getattr(source_function, 'calls', 0) or 0),
            'calling': int(getattr(source_function, 'calling', 0) or 0),
        }
        
        func_code = _get_function_code(file_path, source_function.start_line, source_function.end_line)
        
        if func_code:
            try:
                func_dict['max_depth'] = FileAnalyzer._calculate_block_depth_accurate(func_code)
                parser_result = CodeParser.parse_c_like_code(func_code)
                func_dict['has_complex_preprocessor'] = parser_result.get('has_complex_preprocessor', False)
                func_dict['balanced_blocks'] = parser_result.get('balanced_blocks', False)
            except Exception as e:
                print(f"Warning: Failed to analyze function {source_function.name}: {str(e)}")
                func_dict['max_depth'] = 0
                func_dict['has_complex_preprocessor'] = True
                func_dict['balanced_blocks'] = False
        else:
            func_dict['max_depth'] = 0
            func_dict['has_complex_preprocessor'] = False
            func_dict['balanced_blocks'] = True
            
        func_dict['in_disable_block'] = _is_in_disable_block(file_path, source_function.start_line, source_function.end_line)
            
        return func_dict
        
    except Exception as e:
        print(f"Error creating dict for function {source_function.name}: {str(e)}")
        return {
            'name': source_function.name,
            'cyclomatic_complexity': getattr(source_function, 'cyclomatic_complexity', 0),
            'cognitive_complexity': int(
                getattr(source_function, 'cognitive_complexity', 0) or 0),
            'max_nesting_depth': int(
                getattr(source_function, 'max_nesting_depth', 0) or 0),
            'nloc': getattr(source_function, 'nloc', 0),
            'token_count': getattr(source_function, 'token_count', 0),
            'parameter_count': getattr(source_function, 'parameter_count', 0),
            'start_line': getattr(source_function, 'start_line', 0),
            'end_line': getattr(source_function, 'end_line', 0),
            'max_depth': 0,
            'has_complex_preprocessor': True,
            'balanced_blocks': False,
            'in_disable_block': False
        }

def _is_in_disable_block(file_path, start_line, end_line):
    """Проверяет, находится ли функция между XLIZARD_DISABLE и XLIZARD_ENABLE"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        in_disable_block = False
        disable_start = 0
        
        for i, line in enumerate(lines[:start_line], 1):
            if 'XLIZARD_DISABLE' in line:
                in_disable_block = True
                disable_start = i
            elif 'XLIZARD_ENABLE' in line and in_disable_block:
                in_disable_block = False
                
        if in_disable_block:
            return True
            
        for i, line in enumerate(lines[start_line-1:end_line], start_line):
            if 'XLIZARD_DISABLE' in line:
                return True
                
    except Exception:
        pass
        
    return False


TEMPLATE = '''<!DOCTYPE HTML PUBLIC
"-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
 <head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
        --glass-bg: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
        --glass-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.2);
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --warning-gradient: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%);
        --danger-gradient: linear-gradient(135deg, #ff057c 0%, #8d0b93 100%);
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.8);
        --text-tertiary: rgba(255, 255, 255, 0.6);
        --bg-primary: #0f0f1a;
        --bg-secondary: #1a1a2a;
        --border-radius: 12px;
        --border-radius-sm: 6px;
        
        /* Badge colors for dark theme */
        --badge-safe-bg: rgba(67, 233, 123, 0.15);
        --badge-safe-border: rgba(67, 233, 123, 0.4);
        --badge-safe-text: #43e97b;
        
        --badge-warning-bg: rgba(255, 152, 0, 0.15);
        --badge-warning-border: rgba(255, 152, 0, 0.4);
        --badge-warning-text: #ff9800;
        
        --badge-danger-bg: rgba(255, 5, 124, 0.15);
        --badge-danger-border: rgba(255, 5, 124, 0.4);
        --badge-danger-text: #ff057c;
        
        --badge-info-bg: rgba(79, 172, 254, 0.15);
        --badge-info-border: rgba(79, 172, 254, 0.4);
        --badge-info-text: #4facfe;

        /* Navigation colors for dark theme */
        --nav-bg: rgba(255, 255, 255, 0.05);
        --nav-border: rgba(255, 255, 255, 0.1);
        --nav-text: rgba(255, 255, 255, 0.8);
        --nav-active-bg: rgba(103, 126, 234, 0.2);
        --nav-active-border: rgba(103, 126, 234, 0.4);
        --nav-active-text: #ffffff;
    }

    [data-theme="light"] {
        --glass-bg: rgba(255, 255, 255, 0.8);
        --glass-border: rgba(0, 0, 0, 0.1);
        --glass-shadow: 0 4px 12px 0 rgba(0, 0, 0, 0.1);
        --text-primary: #1a1a2a;
        --text-secondary: rgba(26, 26, 42, 0.8);
        --text-tertiary: rgba(26, 26, 42, 0.6);
        --bg-primary: #f8f9fa;
        --bg-secondary: #ffffff;
        
        /* Badge colors for light theme */
        --badge-safe-bg: rgba(67, 233, 123, 0.15);
        --badge-safe-border: rgba(67, 233, 123, 0.5);
        --badge-safe-text: #27ae60;
        
        --badge-warning-bg: rgba(255, 152, 0, 0.15);
        --badge-warning-border: rgba(255, 152, 0, 0.5);
        --badge-warning-text: #ff9800;
        
        --badge-danger-bg: rgba(255, 5, 124, 0.15);
        --badge-danger-border: rgba(255, 5, 124, 0.5);
        --badge-danger-text: #c0392b;
        
        --badge-info-bg: rgba(79, 172, 254, 0.15);
        --badge-info-border: rgba(79, 172, 254, 0.5);
        --badge-info-text: #2980b9;

        /* Navigation colors for light theme */
        --nav-bg: rgba(0, 0, 0, 0.05);
        --nav-border: rgba(0, 0, 0, 0.1);
        --nav-text: rgba(26, 26, 42, 0.8);
        --nav-active-bg: rgba(103, 126, 234, 0.15);
        --nav-active-border: rgba(103, 126, 234, 0.3);
        --nav-active-text: #667eea;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    body {
        font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.5;
        min-height: 100vh;
        overflow-x: auto;
        transition: all 0.3s ease;
    }

    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }

    /* Glass Elements */
    .glass-header, .glass-nav, .glass-card, .metric-card, .chart-container, .directory-header, .file-card, .glass-search, .glass-footer {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius);
        box-shadow: var(--glass-shadow);
    }

    /* Scroll to Top Button */
    .scroll-to-top {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        background: var(--primary-gradient);
        border: none;
        border-radius: 50%;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        opacity: 0;
        visibility: hidden;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 1000;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .scroll-to-top.visible {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }

    .scroll-to-top:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
    }

    .scroll-to-top:active {
        transform: translateY(0);
    }

    .glass-header {
        padding: 1.5rem;
        margin-bottom: 1rem;
        position: relative;
        overflow: hidden;
    }

    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        position: relative;
        z-index: 2;
    }

    .header-text {
        flex: 1;
    }

    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    .logo {
        width: 40px;
        height: 40px;
        background: var(--primary-gradient);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: white;
    }

    .report-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }

    .report-subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }

    .header-meta {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .meta-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .header-actions {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }

    .glass-button {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        color: var(--text-primary);
        padding: 0.5rem 1rem;
        border-radius: var(--border-radius-sm);
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .glass-button:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    /* Navigation */
    .glass-nav {
        display: flex;
        padding: 0.5rem;
        margin-bottom: 1rem;
        gap: 0.5rem;
        background: var(--nav-bg);
        border: 1px solid var(--nav-border);
    }

    .nav-item {
        padding: 0.75rem 1.5rem;
        cursor: pointer;
        border-radius: var(--border-radius-sm);
        transition: all 0.2s ease;
        color: var(--nav-text);
        font-weight: 500;
        border: none;
        background: none;
        flex: 1;
        text-align: center;
        border: 1px solid transparent;
    }

    .nav-item:hover {
        color: var(--text-primary);
        background: rgba(255, 255, 255, 0.05);
        border-color: var(--nav-border);
    }

    .nav-item.active {
        color: var(--nav-active-text);
        background: var(--nav-active-bg);
        font-weight: 600;
        border-color: var(--nav-active-border);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    /* Cards */
    .glass-card {
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--glass-border);
    }

    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .quality-card .quality-body {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        align-items: flex-start;
    }

    .quality-score-block {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
        min-width: 140px;
    }

    .quality-score-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
        color: var(--text-primary);
    }

    .quality-details {
        flex: 1;
        min-width: 220px;
    }

    .quality-meta {
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }

    .quality-top-list {
        margin: 0;
        padding-left: 1.2rem;
        color: var(--text-primary);
        font-size: 0.95rem;
    }

    .quality-top-list li {
        margin-bottom: 0.25rem;
    }

    .quality-formula {
        margin-top: 0.75rem;
        padding: 0.75rem 0.9rem;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--glass-border);
        font-family: 'Consolas', 'Fira Code', monospace;
        font-size: 0.82rem;
        line-height: 1.45;
        color: var(--text-primary);
        white-space: pre-wrap;
        word-break: break-word;
    }

    .quality-formula-note {
        margin-top: 0.4rem;
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 0.8rem;
        color: var(--text-secondary);
        white-space: normal;
    }

    .quality-top-hint {
        color: var(--text-secondary);
        font-size: 0.85rem;
    }

    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s ease;
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius);
        box-shadow: var(--glass-shadow);
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }

    .metric-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.5rem 0;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* Charts */
    .charts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .chart-container {
        padding: 1.5rem;
        transition: all 0.2s ease;
    }

    .chart-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }

    .chart-wrapper {
        position: relative;
        height: 250px;
        width: 100%;
    }

    /* Directory Groups */
    .directory-group {
        margin-bottom: 1.5rem;
    }

    .directory-header {
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .directory-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .directory-count {
        background: var(--primary-gradient);
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
    }

    /* File Cards */
    .file-card {
        margin-bottom: 1rem;
        overflow: hidden;
        transition: all 0.2s ease;
    }

    .file-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 1rem 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        background: rgba(255, 255, 255, 0.02);
        flex-direction: column;
        gap: 0.75rem;
    }

    .file-header:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .file-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        width: 100%;
    }

    .file-icon {
        width: 20px;
        height: 20px;
        background: var(--primary-gradient);
        mask: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"/></svg>');
        -webkit-mask: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6z"/></svg>');
        mask-repeat: no-repeat;
        -webkit-mask-repeat: no-repeat;
        flex-shrink: 0;
    }

    .file-name {
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        flex: 1;
    }

    .file-metrics {
        display: flex;
        gap: 0.5rem;
        width: 100%;
        flex-wrap: wrap;
    }

    /* Badges */
    .glass-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        transition: all 0.2s ease;
        white-space: nowrap;
        position: relative;
        border: 1px solid;
        backdrop-filter: none;
    }

    .glass-badge.safe {
        background: var(--badge-safe-bg);
        border-color: var(--badge-safe-border);
        color: var(--badge-safe-text);
    }

    .glass-badge.warning {
        background: var(--badge-warning-bg);
        border-color: var(--badge-warning-border);
        color: var(--badge-warning-text);
    }

    .glass-badge.danger {
        background: var(--badge-danger-bg);
        border-color: var(--badge-danger-border);
        color: var(--badge-danger-text);
    }

    .glass-badge.info {
        background: var(--badge-info-bg);
        border-color: var(--badge-info-border);
        color: var(--badge-info-text);
    }

    .glass-badge:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }

    .badge-value {
        font-weight: 700;
        margin-right: 0.25rem;
    }

    .badge-label {
        font-size: 0.75rem;
        opacity: 0.9;
    }

    .file-content {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
        background: rgba(255, 255, 255, 0.02);
    }

    .file-content.expanded {
        max-height: none;
        overflow-x: auto;
        overflow-y: visible;
    }

    .table-scroll {
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        overflow-y: visible;
        -webkit-overflow-scrolling: touch;
        padding-bottom: 0.35rem;
    }

    .file-table {
        width: max-content;
        min-width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
    }

    .file-summary-table {
        margin-bottom: 0.75rem;
        border-bottom: 1px solid var(--glass-border);
    }

    .file-table th {
        text-align: left;
        padding: 1rem 1.5rem;
        font-weight: 600;
        color: var(--text-secondary);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid var(--glass-border);
        white-space: nowrap;
    }

    .file-table td {
        padding: 0.75rem 1.5rem;
        border-bottom: 1px solid var(--glass-border);
        white-space: nowrap;
    }

    .file-table tr:last-child td {
        border-bottom: none;
    }

    .function-name {
        font-family: 'Fira Code', 'Consolas', monospace;
        color: var(--text-primary);
        font-size: 0.9rem;
    }

    .metric-value-high {
        color: #ff057c;
        font-weight: 600;
    }

    .metric-value-low {
        color: #43e97b;
        font-weight: 500;
    }

    .metric-value-warning {
        color: #ff9800;
        font-weight: 600;
    }

    .function-disabled {
        background: rgba(255, 165, 0, 0.05);
        border-left: 3px solid #ff8c00;
    }

    .function-preprocessor {
        background: rgba(255, 152, 0, 0.08);
        border-left: 3px solid #ff9800;
    }

    .function-unbalanced {
        background: rgba(255, 5, 124, 0.08);
        border-left: 3px solid #ff057c;
    }

    /* Tooltips */
    .tooltip-icon {
        cursor: pointer;
        width: 16px;
        height: 16px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        color: var(--text-secondary);
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: 0.25rem;
        transition: all 0.2s ease;
    }

    .tooltip-icon:hover {
        background: var(--primary-gradient);
        color: white;
        border-color: transparent;
    }

    .custom-tooltip {
        position: absolute;
        z-index: 1000;
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        color: var(--text-primary);
        padding: 0.75rem 1rem;
        border-radius: var(--border-radius-sm);
        font-size: 0.8rem;
        max-width: 250px;
        box-shadow: var(--glass-shadow);
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.2s ease;
        pointer-events: none;
        line-height: 1.4;
    }

    .custom-tooltip.visible {
        opacity: 1;
        transform: translateY(0);
    }

    /* Search */
    .glass-search {
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .search-container {
        display: flex;
        align-items: center;
        position: relative;
    }

    .search-icon {
        position: absolute;
        left: 12px;
        color: var(--text-secondary);
        z-index: 2;
    }

    .search-input {
        width: 100%;
        padding: 0.75rem 2.5rem;
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid var(--glass-border);
        border-radius: var(--border-radius-sm);
        color: var(--text-primary);
        font-family: inherit;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }

    .search-input:focus {
        outline: none;
        border-color: rgba(103, 126, 234, 0.5);
        background: rgba(255, 255, 255, 0.15);
    }

    .clear-search {
        position: absolute;
        right: 12px;
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
    }

    /* Search highlight */
    .highlight {
        background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
        color: #000 !important;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: 600;
    }

    .search-match {
        animation: highlightPulse 2s ease-in-out;
    }

    @keyframes highlightPulse {
        0%, 100% { background-color: transparent; }
        50% { background-color: rgba(255, 215, 0, 0.3); }
    }

    /* Footer */
    .glass-footer {
        padding: 1.5rem;
        margin-top: 2rem;
        text-align: center;
        color: var(--text-secondary);
    }

    .glass-footer a {
        color: var(--text-primary);
        text-decoration: none;
        font-weight: 500;
        background: var(--primary-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* Tab Content */
    .tab-content {
        display: none;
    }

    .tab-content.active {
        display: block;
        animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    /* Performance Optimizations */
    .chart-container canvas {
        max-width: 100%;
        height: auto;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .container {
            padding: 0.5rem;
        }
        
        .glass-header {
            padding: 1rem;
        }
        
        .header-content {
            flex-direction: column;
        }
        
        .report-title {
            font-size: 1.5rem;
        }
        
        .metrics-grid {
            grid-template-columns: 1fr 1fr;
        }
        
        .charts-grid {
            grid-template-columns: 1fr;
        }
        
        .chart-wrapper {
            height: 200px;
        }
        
        .file-header {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .file-metrics {
            justify-content: flex-start;
        }
        
        .glass-nav {
            flex-direction: column;
        }
        
        .scroll-to-top {
            bottom: 20px;
            right: 20px;
            width: 45px;
            height: 45px;
            font-size: 18px;
        }
    }

    @media (max-width: 480px) {
        .metrics-grid {
            grid-template-columns: 1fr;
        }
        
        .file-table {
            font-size: 0.8rem;
        }
        
        .file-table th,
        .file-table td {
            padding: 0.5rem 1rem;
        }
        
        .file-metrics {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .glass-badge {
            width: 100%;
            justify-content: space-between;
        }
        
        .scroll-to-top {
            bottom: 15px;
            right: 15px;
            width: 40px;
            height: 40px;
            font-size: 16px;
        }
    }
  </style>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Scroll to Top Button -->
    <button class="scroll-to-top" id="scrollToTop" aria-label="Scroll to top">
        ↑
    </button>

    <div class="container">
        <!-- Glass Header -->
        <div class="glass-header">
            <div class="header-content">
                <div class="header-text">
                    <div class="logo-container">
                        <div class="logo">🦎</div>
                        <h1 class="report-title">{{ title }}</h1>
                    </div>
                    <p class="report-subtitle">Отчёт анализа качества кода</p>
                    <div class="header-meta">
                        <div class="meta-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                            </svg>
                            {{ total_files }} файлов
                        </div>
                        <div class="meta-item">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/>
                                <path d="M12.5 7H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                            </svg>
                            {{ date }}
                        </div>
                    </div>
                </div>
                <div class="header-actions">
                    <button class="glass-button" id="themeToggle">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69zM12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/>
                        </svg>
                        Тема
                    </button>
                </div>
            </div>
        </div>

        <!-- Navigation -->
        <div class="glass-nav">
            <button class="nav-item active" data-tab="dashboardTab">Обзор</button>
            <button class="nav-item" data-tab="filesTab">Файлы</button>
            <button class="nav-item" data-tab="advancedTab">Подробности</button>
        </div>

        <!-- Search -->
        <div class="glass-search">
            <div class="search-container">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="search-icon">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <input type="text" id="searchInput" placeholder="Поиск файлов и функций…" class="search-input">
                <button id="clearSearch" class="clear-search" style="display: none;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Dashboard Tab -->
        <div class="tab-content active" id="dashboardTab">
            <!-- Quality score -->
            <div class="glass-card quality-card">
                <div class="card-header">
                    <h3 class="card-title">Суммарная оценка качества</h3>
                    <div class="tooltip-icon" data-tooltip="Балл 0–100 по порогам из xlizard.json / «Пороги». Формула и веса настраиваются в quality_score. Мягкое превышение — не более soft% над лимитом метрики. Жёсткое — сильнее.">?</div>
                </div>
                <div class="quality-body">
                    <div class="quality-score-block">
                        <div class="quality-score-value">{{ quality.score }}</div>
                        <div class="glass-badge {{ quality.status_class }}">
                            <span class="badge-label">{{ quality.status }}</span>
                        </div>
                        {% if quality.has_exceedances %}
                        <div class="glass-badge warning">
                            <span class="badge-label">есть превышения</span>
                        </div>
                        {% endif %}
                        {% if his_metrics %}
                        <div class="glass-badge info">
                            <span class="badge-label">HIS вкл.</span>
                        </div>
                        {% else %}
                        <div class="glass-badge warning">
                            <span class="badge-label">HIS откл.</span>
                        </div>
                        {% endif %}
                    </div>
                    <div class="quality-details">
                        {% if not his_metrics %}
                        <div class="quality-meta">
                            HIS-метрики отключены (GOTO / RETURN / PATH / CALLS / CALLING).
                            Включить: Пороги → чекбокс HIS.
                        </div>
                        {% endif %}
                        <div class="quality-meta">
                            Мягких: {{ quality.soft_count }} · Жёстких: {{ quality.hard_count }} · Функций: {{ quality.total_functions }}
                            · Доля мягк. {{ (quality.soft_func_rate * 100)|round(1) }}%
                            · Доля жёстк. {{ (quality.hard_func_rate * 100)|round(1) }}%
                            · Штраф файлов: {{ quality.file_penalty|default(0)|round(1) }}
                        </div>
                        <div class="quality-formula">{{ quality.formula }}
<div class="quality-formula-note">{{ quality.formula_detail }} Веса: мягк.ф.={{ quality.weights.soft_func_weight }}, жёстк.ф.={{ quality.weights.hard_func_weight }}, файл мягк.={{ quality.weights.file_soft_penalty }}, файл жёстк.={{ quality.weights.file_hard_penalty }}, потолок={{ quality.weights.file_penalty_cap }}. Изменить: «Пороги» или xlizard.json → quality_score.</div>
                        </div>
                        {% if quality.top_exceedances %}
                        <ul class="quality-top-list">
                            {% for item in quality.top_exceedances %}
                            <li>
                                {{ item.label }}:
                                {% if item.soft %}{{ item.soft }} мягк.{% endif %}
                                {% if item.soft and item.hard %}, {% endif %}
                                {% if item.hard %}{{ item.hard }} жёстк.{% endif %}
                                <span class="quality-top-hint">(лимит {{ item.limit }}, мягкое {{ item.soft_pct }}%)</span>
                            </li>
                            {% endfor %}
                        </ul>
                        {% else %}
                        <div class="quality-meta">Превышений порогов нет.</div>
                        {% endif %}
                    </div>
                </div>
            </div>

            <!-- Metrics Cards -->
            <div class="glass-card">
                <div class="card-header">
                    <h3 class="card-title">Обзор проекта</h3>
                </div>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">📊</div>
                        <div class="metric-value">{{ avg_complexity|round(1) }}</div>
                        <div class="metric-label">Средняя сложность (CCN)</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">💬</div>
                        <div class="metric-value">{{ avg_comments|round(1) }}%</div>
                        <div class="metric-label">Средняя доля комментариев</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">📏</div>
                        <div class="metric-value">{{ avg_depth|round(1) }}</div>
                        <div class="metric-label">Средняя глубина блоков</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">⚡</div>
                        <div class="metric-value">{{ total_functions }}</div>
                        <div class="metric-label">Всего функций</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">🔧</div>
                        <div class="metric-value">{{ total_disabled_functions }}</div>
                        <div class="metric-label">Отключённые функции</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-icon">⚠️</div>
                        <div class="metric-value">{{ problem_files }}</div>
                        <div class="metric-label">Проблемные файлы</div>
                    </div>
                </div>
            </div>

            <!-- Charts -->
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">Распределение сложности (CCN)</div>
                    <div class="chart-wrapper">
                        <canvas id="complexityChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Обзор метрик</div>
                    <div class="chart-wrapper">
                        <canvas id="metricsChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Распределение комментариев</div>
                    <div class="chart-wrapper">
                        <canvas id="commentsChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Глубина и указатели</div>
                    <div class="chart-wrapper">
                        <canvas id="depthPointersChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Files Tab -->
        <div class="tab-content" id="filesTab">
            <div class="glass-card">
                <div class="card-header">
                    <h3 class="card-title">Файлы проекта</h3>
                    <div class="directory-count">{{ total_files }} файлов</div>
                </div>
                {% if not his_metrics %}
                <div class="quality-meta" style="margin-bottom: 1rem;">
                    HIS-метрики отключены (GOTO / RETURN / PATH / CALLS / CALLING) — колонки не показаны.
                    Включить: Пороги → чекбокс HIS.
                </div>
                {% endif %}
                
                {% for dirname, files in dir_groups.items() %}
                <div class="directory-group">
                    <div class="directory-header">
                        <h3 class="directory-name">{{ dirname }}</h3>
                        <div class="directory-count">{{ files|length }} файлов</div>
                    </div>
                    
                    {% for file in files %}
                    <div class="file-card">
                        <div class="file-header" onclick="toggleFile(this)">
                            <div class="file-title">
                                <div class="file-icon"></div>
                                <h4 class="file-name">{{ file.basename }}</h4>
                            </div>
                            <div class="file-metrics">
                                <div class="glass-badge {% if file.max_complexity <= thresholds.cyclomatic_complexity*0.5 %}safe{% elif file.max_complexity <= thresholds.cyclomatic_complexity %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.max_complexity }}</span>
                                    <span class="badge-label">Макс. CCN</span>
                                    <div class="tooltip-icon" data-tooltip="Пороги CCN: ≤{{ (thresholds.cyclomatic_complexity*0.5)|round }} (норма), ≤{{ thresholds.cyclomatic_complexity }} (внимание), >{{ thresholds.cyclomatic_complexity }} (превышение). Мягкое: {{ soft_pcts.cyclomatic_complexity|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge {% if file.active_functions_count <= thresholds.function_count*0.5 %}safe{% elif file.active_functions_count <= thresholds.function_count %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.active_functions_count }}</span>
                                    <span class="badge-label">Функции</span>
                                    <div class="tooltip-icon" data-tooltip="Пороги числа функций: ≤{{ (thresholds.function_count*0.5)|round }} (норма), ≤{{ thresholds.function_count }} (внимание), >{{ thresholds.function_count }} (превышение). Мягкое: {{ soft_pcts.function_count|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge {% if file.disabled_functions_count > 0 %}warning{% else %}safe{% endif %}">
                                    <span class="badge-value">{{ file.disabled_functions_count }}</span>
                                    <span class="badge-label">Откл.</span>
                                    <div class="tooltip-icon" data-tooltip="Функции внутри XLIZARD_DISABLE / XLIZARD_ENABLE">?</div>
                                </div>
                                <div class="glass-badge {% if file.max_block_depth <= thresholds.max_block_depth*0.7 %}safe{% elif file.max_block_depth <= thresholds.max_block_depth %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.max_block_depth }}</span>
                                    <span class="badge-label">Глубина</span>
                                    <div class="tooltip-icon" data-tooltip="Пороги глубины блоков: ≤{{ (thresholds.max_block_depth*0.7)|round }} (норма), ≤{{ thresholds.max_block_depth }} (внимание), >{{ thresholds.max_block_depth }} (превышение). Мягкое: {{ soft_pcts.max_block_depth|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge {% if file.pointer_operations <= thresholds.pointer_operations*0.5 %}safe{% elif file.pointer_operations <= thresholds.pointer_operations %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.pointer_operations }}</span>
                                    <span class="badge-label">Указатели</span>
                                    <div class="tooltip-icon" data-tooltip="Пороги операций с указателями: ≤{{ (thresholds.pointer_operations*0.5)|round }} (норма), ≤{{ thresholds.pointer_operations }} (внимание), >{{ thresholds.pointer_operations }} (превышение). Мягкое: {{ soft_pcts.pointer_operations|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge {% if file.preprocessor_directives <= thresholds.preprocessor_directives*0.5 %}safe{% elif file.preprocessor_directives <= thresholds.preprocessor_directives %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.preprocessor_directives }}</span>
                                    <span class="badge-label">ПП</span>
                                    <div class="tooltip-icon" data-tooltip="Пороги директив препроцессора: ≤{{ (thresholds.preprocessor_directives*0.5)|round }} (норма), ≤{{ thresholds.preprocessor_directives }} (внимание), >{{ thresholds.preprocessor_directives }} (превышение). Мягкое: {{ soft_pcts.preprocessor_directives|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge info">
                                    <span class="badge-value">{{ file.comment_percentage|round(1) }}%</span>
                                    <span class="badge-label">Коммент.</span>
                                </div>
                                <div class="glass-badge {% if file.logical_operators <= thresholds.logical_operators*0.5 %}safe{% elif file.logical_operators <= thresholds.logical_operators %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.logical_operators }}</span>
                                    <span class="badge-label">Logic</span>
                                    <div class="tooltip-icon" data-tooltip="Логические операторы && || ! по файлу. Порог: {{ thresholds.logical_operators }}. Мягкое: {{ soft_pcts.logical_operators|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge {% if file.conditional_statements <= thresholds.conditional_statements*0.5 %}safe{% elif file.conditional_statements <= thresholds.conditional_statements %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.conditional_statements }}</span>
                                    <span class="badge-label">Cond</span>
                                    <div class="tooltip-icon" data-tooltip="Условные операторы (if/for/while/…) по файлу. Порог: {{ thresholds.conditional_statements }}. Мягкое: {{ soft_pcts.conditional_statements|default(25)|int }}%">?</div>
                                </div>
                                <div class="glass-badge info">
                                    <span class="badge-value">{{ file.lines_of_code }}</span>
                                    <span class="badge-label">LOC</span>
                                    <div class="tooltip-icon" data-tooltip="Строки кода файла (без пустых и чисто комментарных). Всего строк: {{ file.total_lines }}, комментариев: {{ file.comment_lines }}">?</div>
                                </div>
                                <div class="glass-badge {% if file.avg_complexity <= thresholds.cyclomatic_complexity*0.5 %}safe{% elif file.avg_complexity <= thresholds.cyclomatic_complexity %}warning{% else %}danger{% endif %}">
                                    <span class="badge-value">{{ file.avg_complexity|round(1) }}</span>
                                    <span class="badge-label">Ср. CCN</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="file-content">
                            <div class="table-scroll">
                            <table class="file-table file-summary-table">
                                <thead>
                                    <tr>
                                        <th>Сводка файла</th>
                                        <th>Макс. CCN</th>
                                        <th>Ср. CCN</th>
                                        <th>Функции</th>
                                        <th>Откл.</th>
                                        <th>Проблемные</th>
                                        <th>Глубина</th>
                                        <th>Указатели</th>
                                        <th>ПП</th>
                                        <th>Logic</th>
                                        <th>Cond</th>
                                        <th>LOC</th>
                                        <th>Коммент.</th>
                                        <th>Всего строк</th>
                                        <th>Коммент. %</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td class="function-name">{{ file.basename }}</td>
                                        <td class="{% if file.max_complexity > thresholds.cyclomatic_complexity %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.max_complexity }}</td>
                                        <td class="{% if file.avg_complexity > thresholds.cyclomatic_complexity %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.avg_complexity|round(1) }}</td>
                                        <td class="{% if file.active_functions_count > thresholds.function_count %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.active_functions_count }}</td>
                                        <td class="{% if file.disabled_functions_count > 0 %}metric-value-warning{% else %}metric-value-low{% endif %}">{{ file.disabled_functions_count }}</td>
                                        <td class="{% if file.problem_functions > 0 %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.problem_functions }}</td>
                                        <td class="{% if file.max_block_depth > thresholds.max_block_depth %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.max_block_depth }}</td>
                                        <td class="{% if file.pointer_operations > thresholds.pointer_operations %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.pointer_operations }}</td>
                                        <td class="{% if file.preprocessor_directives > thresholds.preprocessor_directives %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.preprocessor_directives }}</td>
                                        <td class="{% if file.logical_operators > thresholds.logical_operators %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.logical_operators }}</td>
                                        <td class="{% if file.conditional_statements > thresholds.conditional_statements %}metric-value-high{% else %}metric-value-low{% endif %}">{{ file.conditional_statements }}</td>
                                        <td class="metric-value-low">{{ file.lines_of_code }}</td>
                                        <td class="metric-value-low">{{ file.comment_lines }}</td>
                                        <td class="metric-value-low">{{ file.total_lines }}</td>
                                        <td class="metric-value-low">{{ file.comment_percentage|round(1) }}%</td>
                                    </tr>
                                </tbody>
                            </table>
                            </div>
                            {% if file.functions %}
                            <div class="table-scroll">
                            <table class="file-table">
                                <thead>
                                    <tr>
                                        <th>Функция</th>
                                        <th>Строки</th>
                                        <th>
                                            Цикл. сложность (CCN) <div class="tooltip-icon" data-tooltip="Цикломатическая сложность. Порог: {{ thresholds.cyclomatic_complexity }}. Мягкое: {{ soft_pcts.cyclomatic_complexity|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Когн. сложность (CogC) <div class="tooltip-icon" data-tooltip="Когнитивная сложность (SonarSource). Порог: {{ thresholds.cognitive_complexity|default(25) }}. Мягкое: {{ soft_pcts.cognitive_complexity|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Строки кода (NLOC) <div class="tooltip-icon" data-tooltip="Строки кода без комментариев. Порог: {{ thresholds.nloc }}. Мягкое: {{ soft_pcts.nloc|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Длина (Length) <div class="tooltip-icon" data-tooltip="Строки исходника от начала до конца функции. Порог: {{ thresholds.length|default(150) }}. Мягкое: {{ soft_pcts.length|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Токены (Tokens) <div class="tooltip-icon" data-tooltip="Число токенов. Порог: {{ thresholds.token_count }}. Мягкое: {{ soft_pcts.token_count|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Параметры (PARAM) <div class="tooltip-icon" data-tooltip="Число параметров. Порог: {{ thresholds.parameter_count }}. Мягкое: {{ soft_pcts.parameter_count|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Вложенность (ND) <div class="tooltip-icon" data-tooltip="Глубина вложенности управляющих конструкций. Порог: {{ thresholds.max_nesting_depth|default(5) }}. Мягкое: {{ soft_pcts.max_nesting_depth|default(25)|int }}%">?</div>
                                        </th>
                                        <th>
                                            Глубина блоков <div class="tooltip-icon" data-tooltip="Максимальная глубина блоков { }. Порог: {{ thresholds.max_block_depth }}. Мягкое: {{ soft_pcts.max_block_depth|default(25)|int }}%">?</div>
                                        </th>
                                        {% if his_metrics %}
                                        <th>GOTO <div class="tooltip-icon" data-tooltip="HIS GOTO. Порог: {{ thresholds.goto_count|default(0) }}. Мягкое: {{ soft_pcts.goto_count|default(1)|int }}%">?</div></th>
                                        <th>RETURN <div class="tooltip-icon" data-tooltip="HIS RETURN. Порог: {{ thresholds.return_count|default(1) }}. Мягкое: {{ soft_pcts.return_count|default(1)|int }}%">?</div></th>
                                        <th>PATH <div class="tooltip-icon" data-tooltip="HIS PATH (оценка). Порог: {{ thresholds.path_count|default(80) }}. Мягкое: {{ soft_pcts.path_count|default(25)|int }}%">?</div></th>
                                        <th>CALLS <div class="tooltip-icon" data-tooltip="HIS CALLS. Порог: {{ thresholds.calls|default(7) }}. Мягкое: {{ soft_pcts.calls|default(25)|int }}%">?</div></th>
                                        <th>CALLING <div class="tooltip-icon" data-tooltip="HIS CALLING. Порог: {{ thresholds.calling|default(5) }}. Мягкое: {{ soft_pcts.calling|default(25)|int }}%">?</div></th>
                                        {% endif %}
                                        <th>
                                            Статус <div class="tooltip-icon" data-tooltip="Статус анализа функции">?</div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for func in file.functions %}
                                    <tr class="{% if func.in_disable_block %}function-disabled{% elif func.has_complex_preprocessor %}function-preprocessor{% elif not func.balanced_blocks %}function-unbalanced{% endif %}">
                                        <td class="function-name">
                                            {{ func.name }}
                                            {% if func.in_disable_block %}
                                            <div class="tooltip-icon" data-tooltip="Анализ отключён директивой XLIZARD_DISABLE">🟠</div>
                                            {% elif func.has_complex_preprocessor %}
                                            <div class="tooltip-icon" data-tooltip="Пропущено из‑за сложных директив препроцессора">🔶</div>
                                            {% elif not func.balanced_blocks %}
                                            <div class="tooltip-icon" data-tooltip="Несбалансированные скобки — анализ может быть неполным">⚠️</div>
                                            {% endif %}
                                        </td>
                                        <td class="metric-value-low">{{ func.start_line|default(0) }}–{{ func.end_line|default(0) }}</td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif func.cyclomatic_complexity > thresholds.cyclomatic_complexity %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.cyclomatic_complexity }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.cognitive_complexity|default(0)) > (thresholds.cognitive_complexity|default(25)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.cognitive_complexity|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif func.nloc > thresholds.nloc %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.nloc }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.length|default(0)) > (thresholds.length|default(150)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.length|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif func.token_count > thresholds.token_count %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.token_count }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif func.parameter_count > thresholds.parameter_count %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.parameter_count }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.max_nesting_depth|default(0)) > (thresholds.max_nesting_depth|default(5)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.max_nesting_depth|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif func.max_depth > thresholds.max_block_depth %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.max_depth }}
                                        </td>
                                        {% if his_metrics %}
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.goto_count|default(0)) > (thresholds.goto_count|default(0)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.goto_count|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.return_count|default(0)) > (thresholds.return_count|default(1)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.return_count|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.path_count|default(1)) > (thresholds.path_count|default(80)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.path_count|default(1) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.calls|default(0)) > (thresholds.calls|default(7)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.calls|default(0) }}
                                        </td>
                                        <td class="{% if func.in_disable_block or func.has_complex_preprocessor or not func.balanced_blocks %}metric-value-warning{% elif (func.calling|default(0)) > (thresholds.calling|default(5)) %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {{ func.calling|default(0) }}
                                        </td>
                                        {% endif %}
                                        <td class="{% if func.in_disable_block %}metric-value-warning{% elif func.has_complex_preprocessor %}metric-value-warning{% elif not func.balanced_blocks %}metric-value-high{% else %}metric-value-low{% endif %}">
                                            {% if func.in_disable_block %}
                                            Отключена
                                            {% elif func.has_complex_preprocessor %}
                                            Пропущена (ПП)
                                            {% elif not func.balanced_blocks %}
                                            Несбаланс.
                                            {% else %}
                                            Проанализирована
                                            {% endif %}
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            </div>
                            {% else %}
                            <div style="padding: 2rem; text-align: center; color: var(--text-secondary);">
                                Функции не найдены
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Advanced Tab -->
        <div class="tab-content" id="advancedTab">
            <div class="glass-card">
                <div class="card-header">
                    <h3 class="card-title">Самые сложные функции</h3>
                </div>
                <div class="table-scroll">
                    <table class="file-table">
                        <thead>
                            <tr>
                                <th>Функция</th>
                                <th>Файл</th>
                                <th>Сложность (CCN)</th>
                                <th>Строки (NLOC)</th>
                                <th>Статус</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for func in top_complex_functions %}
                            <tr>
                                <td class="function-name">{{ func.name }}</td>
                                <td>{{ func.file }}</td>
                                <td class="metric-value-high">{{ func.complexity }}</td>
                                <td>{{ func.nloc }}</td>
                                <td class="metric-value-low">Проанализирована</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="glass-card">
                <div class="card-header">
                    <h3 class="card-title">Сложность по каталогам</h3>
                </div>
                <div style="overflow-x: auto;">
                    <table class="file-table">
                        <thead>
                            <tr>
                                <th>Каталог</th>
                                <th>Средняя сложность (CCN)</th>
                                <th>Файлы</th>
                                <th>Проблемные функции</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for dir in directory_stats %}
                            <tr>
                                <td>{{ dir.name }}</td>
                                <td class="{% if dir.avg_complexity > thresholds.cyclomatic_complexity %}metric-value-high{% else %}metric-value-low{% endif %}">
                                    {{ dir.avg_complexity|round(1) }}
                                </td>
                                <td>{{ dir.file_count }}</td>
                                <td class="{% if dir.problem_functions > 0 %}metric-value-high{% else %}metric-value-low{% endif %}">
                                    {{ dir.problem_functions }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="glass-footer">
            Сформировано {{ date }} · <a href="http://www.xlizard.ws/" target="_blank">xlizard</a>
        </div>
    </div>

    <script>
    // Global chart instances storage
    const chartInstances = {
        complexityChart: null,
        metricsChart: null,
        commentsChart: null,
        depthPointersChart: null
    };

    // Function to update chart colors based on theme
    function updateChartColors() {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#ffffff' : '#1a1a2a';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        const fontFamily = 'Inter, sans-serif';

        // Update all existing charts
        Object.entries(chartInstances).forEach(([chartName, chart]) => {
            if (chart) {
                // Update scales colors
                if (chart.options.scales) {
                    Object.values(chart.options.scales).forEach(scale => {
                        if (scale.ticks) {
                            scale.ticks.color = textColor;
                        }
                        if (scale.grid) {
                            scale.grid.color = gridColor;
                        }
                        if (scale.title) {
                            scale.title.color = textColor;
                        }
                    });
                }

                // Update legend colors
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels.color = textColor;
                }

                // Update tooltip colors
                if (chart.options.plugins && chart.options.plugins.tooltip) {
                    chart.options.plugins.tooltip.bodyColor = textColor;
                    chart.options.plugins.tooltip.titleColor = textColor;
                }

                chart.update('none'); // Update without animation for better performance
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Initialize charts only when needed
        let chartsInitialized = {
            dashboard: false,
            advanced: false
        };

        // Theme toggle with immediate update
        const themeToggle = document.getElementById('themeToggle');
        
        function applyTheme(theme) {
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            
            // Force CSS repaint
            document.body.style.opacity = '0.99';
            setTimeout(() => {
                document.body.style.opacity = '1';
            }, 10);
            
            // Update charts immediately with proper theme colors
            updateChartColors();
        }

        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.getAttribute('data-theme') || 'dark';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });

        // Set initial theme
        const savedTheme = localStorage.getItem('theme') || 'dark';
        applyTheme(savedTheme);

        // Scroll to Top Functionality
        const scrollToTopBtn = document.getElementById('scrollToTop');

        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollToTopBtn.classList.add('visible');
            } else {
                scrollToTopBtn.classList.remove('visible');
            }
        });

        scrollToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Tooltip system
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        document.body.appendChild(tooltip);

        document.querySelectorAll('.tooltip-icon').forEach(icon => {
            icon.addEventListener('mouseenter', function(e) {
                const text = this.getAttribute('data-tooltip');
                const rect = this.getBoundingClientRect();
                
                tooltip.textContent = text;
                tooltip.style.left = `${rect.left + window.scrollX}px`;
                tooltip.style.top = `${rect.top + window.scrollY - tooltip.offsetHeight - 10}px`;
                tooltip.classList.add('visible');
            });

            icon.addEventListener('mouseleave', function() {
                tooltip.classList.remove('visible');
            });
        });

        // Navigation
        const navItems = document.querySelectorAll('.nav-item');
        const tabContents = document.querySelectorAll('.tab-content');

        function switchTab(tabId) {
            navItems.forEach(nav => nav.classList.remove('active'));
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // Initialize charts for active tab
            if (tabId === 'dashboardTab' && !chartsInitialized.dashboard) {
                initDashboardCharts();
                chartsInitialized.dashboard = true;
            } else if (tabId === 'advancedTab' && !chartsInitialized.advanced) {
                initAdvancedCharts();
                chartsInitialized.advanced = true;
            }
        }

        navItems.forEach(item => {
            item.addEventListener('click', function() {
                switchTab(this.getAttribute('data-tab'));
            });
        });

        // Initialize dashboard charts on first load
        initDashboardCharts();
        chartsInitialized.dashboard = true;

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        const clearSearch = document.getElementById('clearSearch');

        function performSearch() {
            const searchTerm = searchInput.value.toLowerCase().trim();
            clearSearch.style.display = searchTerm ? 'block' : 'none';
            
            // Remove previous highlights
            document.querySelectorAll('.highlight').forEach(el => {
                el.outerHTML = el.innerHTML;
            });
            
            let hasAnyMatch = false;
            let firstMatchElement = null;
            
            if (searchTerm) {
                // Search in file names
                document.querySelectorAll('.file-name').forEach(element => {
                    const filename = element.textContent.toLowerCase();
                    if (filename.includes(searchTerm)) {
                        const highlighted = element.textContent.replace(
                            new RegExp(searchTerm, 'gi'), 
                            match => '<span class="highlight">' + match + '</span>'
                        );
                        element.innerHTML = highlighted;
                        const fileCard = element.closest('.file-card');
                        fileCard.classList.add('search-match');
                        hasAnyMatch = true;
                        
                        // Auto-expand file
                        const fileHeader = fileCard.querySelector('.file-header');
                        if (fileHeader && !fileHeader.classList.contains('expanded')) {
                            toggleFile(fileHeader);
                        }
                        
                        // Remember first match for scrolling
                        if (!firstMatchElement) {
                            firstMatchElement = fileCard;
                        }
                    }
                });
                
                // Search in function names
                document.querySelectorAll('.function-name').forEach(element => {
                    const funcName = element.textContent.toLowerCase();
                    if (funcName.includes(searchTerm)) {
                        const highlighted = element.textContent.replace(
                            new RegExp(searchTerm, 'gi'), 
                            match => '<span class="highlight">' + match + '</span>'
                        );
                        element.innerHTML = highlighted;
                        const fileCard = element.closest('.file-card');
                        fileCard.classList.add('search-match');
                        hasAnyMatch = true;
                        
                        // Auto-expand file
                        const fileHeader = fileCard.querySelector('.file-header');
                        if (fileHeader && !fileHeader.classList.contains('expanded')) {
                            toggleFile(fileHeader);
                        }
                        
                        // Remember first match for scrolling
                        if (!firstMatchElement) {
                            firstMatchElement = element;
                        }
                    }
                });
                
                // Hide files without matches
                document.querySelectorAll('.file-card').forEach(card => {
                    const hasMatch = card.querySelector('.highlight') !== null;
                    card.style.display = hasMatch ? '' : 'none';
                });
                
                // Scroll to first match
                if (firstMatchElement) {
                    setTimeout(() => {
                        firstMatchElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });
                    }, 100);
                }
            } else {
                // Show all files, remove highlights, and collapse all
                document.querySelectorAll('.file-card').forEach(card => {
                    card.style.display = '';
                    card.classList.remove('search-match');
                    
                    // Collapse file if it was expanded by search
                    const fileHeader = card.querySelector('.file-header');
                    if (fileHeader && fileHeader.classList.contains('expanded')) {
                        toggleFile(fileHeader);
                    }
                });
            }
        }

        searchInput.addEventListener('input', performSearch);
        
        clearSearch.addEventListener('click', function() {
            searchInput.value = '';
            clearSearch.style.display = 'none';
            
            // Remove all highlights, show all files, and collapse all
            document.querySelectorAll('.highlight').forEach(el => {
                el.outerHTML = el.innerHTML;
            });
            
            document.querySelectorAll('.file-card').forEach(card => {
                card.style.display = '';
                card.classList.remove('search-match');
                
                // Collapse file if it was expanded by search
                const fileHeader = card.querySelector('.file-header');
                if (fileHeader && fileHeader.classList.contains('expanded')) {
                    toggleFile(fileHeader);
                }
            });
        });

        // Handle Escape key for search
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && searchInput.value) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        });

        // Auto-switch to Files tab when searching
        searchInput.addEventListener('focus', function() {
            if (this.value) {
                switchTab('filesTab');
            }
        });
    });

    function toggleFile(header) {
        const content = header.nextElementSibling;
        const isExpanding = !header.classList.contains('expanded');
        
        header.classList.toggle('expanded');
        content.classList.toggle('expanded');
        
        if (isExpanding) {
            content.style.maxHeight = (content.scrollHeight + 24) + 'px';
            // After transition: allow full height so wide tables can scroll horizontally
            setTimeout(function() {
                if (content.classList.contains('expanded')) {
                    content.style.maxHeight = 'none';
                }
            }, 320);
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
            void content.offsetHeight;
            content.style.maxHeight = '0';
        }
    }

    function initDashboardCharts() {
        const dashboardData = {{ dashboard_data|tojson }};
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        const textColor = isDark ? '#ffffff' : '#1a1a2a';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
        const fontFamily = 'Inter, sans-serif';

        // Destroy existing charts
        Object.values(chartInstances).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });

        // Complexity Distribution
        const complexityCtx = document.getElementById('complexityChart').getContext('2d');
        chartInstances.complexityChart = new Chart(complexityCtx, {
            type: 'doughnut',
            data: {
                labels: ['Низкая', 'Средняя', 'Высокая'],
                datasets: [{
                    data: [
                        dashboardData.complexity_distribution.low,
                        dashboardData.complexity_distribution.medium,
                        dashboardData.complexity_distribution.high
                    ],
                    backgroundColor: ['#43e97b', '#ff9800', '#ff057c']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: textColor,
                            font: {
                                family: fontFamily,
                                size: 12
                            }
                        }
                    }
                }
            }
        });

        // Metrics Comparison
        const metricsCtx = document.getElementById('metricsChart').getContext('2d');
        chartInstances.metricsChart = new Chart(metricsCtx, {
            type: 'bar',
            data: {
                labels: ['Сложность (CCN)', 'Коммент. %', 'Глубина', 'Указатели'],
                datasets: [{
                    label: 'Среднее',
                    data: [
                        dashboardData.avg_metrics.complexity,
                        dashboardData.avg_metrics.comments,
                        dashboardData.avg_metrics.depth,
                        dashboardData.avg_metrics.pointers
                    ],
                    backgroundColor: 'rgba(103, 126, 234, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { 
                            color: gridColor 
                        },
                        ticks: { 
                            color: textColor,
                            font: {
                                family: fontFamily,
                                size: 11
                            }
                        }
                    },
                    x: {
                        grid: { 
                            color: gridColor 
                        },
                        ticks: { 
                            color: textColor,
                            font: {
                                family: fontFamily,
                                size: 11
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: textColor,
                            font: {
                                family: fontFamily,
                                size: 12
                            }
                        }
                    }
                }
            }
        });

        // Comments Distribution
        const commentsCtx = document.getElementById('commentsChart').getContext('2d');
        chartInstances.commentsChart = new Chart(commentsCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(dashboardData.comment_ranges).map(k => k.replace('-', '-') + '%'),
                datasets: [{
                    data: Object.values(dashboardData.comment_ranges),
                    backgroundColor: [
                        'rgba(103, 126, 234, 0.7)',
                        'rgba(67, 233, 123, 0.7)',
                        'rgba(255, 152, 0, 0.7)',
                        'rgba(255, 5, 124, 0.7)',
                        'rgba(79, 172, 254, 0.7)',
                        'rgba(141, 11, 147, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: textColor,
                            font: {
                                family: fontFamily,
                                size: 11
                            }
                        }
                    }
                }
            }
        });

        // Depth vs Pointers Chart
        const depthPointersCtx = document.getElementById('depthPointersChart').getContext('2d');
        if (dashboardData.depth_pointers_data && dashboardData.depth_pointers_data.length > 0) {
            chartInstances.depthPointersChart = new Chart(depthPointersCtx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Файлы',
                        data: dashboardData.depth_pointers_data,
                        backgroundColor: 'rgba(103, 126, 234, 0.7)',
                        borderColor: 'rgba(103, 126, 234, 1)',
                        borderWidth: 1,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            title: {
                                display: true,
                                text: 'Глубина блоков',
                                color: textColor,
                                font: {
                                    family: fontFamily,
                                    size: 12
                                }
                            },
                            grid: { 
                                color: gridColor 
                            },
                            ticks: { 
                                color: textColor,
                                font: {
                                    family: fontFamily,
                                    size: 11
                                }
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Операции с указателями',
                                color: textColor,
                                font: {
                                    family: fontFamily,
                                    size: 12
                                }
                            },
                            grid: { 
                                color: gridColor 
                            },
                            ticks: { 
                                color: textColor,
                                font: {
                                    family: fontFamily,
                                    size: 11
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: textColor,
                                font: {
                                    family: fontFamily,
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'Файл: ' + context.raw.file;
                                },
                                afterLabel: function(context) {
                                    return 'Глубина: ' + context.raw.y + '\\nУказатели: ' + context.raw.x;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    function initAdvancedCharts() {
        // Advanced charts initialization when needed
        console.log('Advanced charts initialized');
    }
    </script>
</body>
</html>'''