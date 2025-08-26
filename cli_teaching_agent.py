#!/usr/bin/env python3
"""CLI interface for the teaching agent"""

import os
import sys
import uuid
import argparse
from datetime import datetime
from typing import Optional
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform colored output
init()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ReAct.teaching_agent_core import SimpleTeachingAgent


class TeachingAgentCLI:
    """Command-line interface for the teaching agent"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.agent = None
        self.session_id = None
    
    def print_welcome(self):
        """Print welcome message"""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🎓 Welcome to the Chinese Teaching Agent! 🎓{Style.RESET_ALL}")
        print(f"{Fore.GREEN}I'm Xiao Lin (小林), your fun Chinese learning buddy!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    def print_help(self):
        """Print help message"""
        print(f"\n{Fore.BLUE}Available Commands:{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}/help{Style.RESET_ALL}    - Show this help message")
        print(f"  {Fore.GREEN}/new{Style.RESET_ALL}     - Start a new session")
        print(f"  {Fore.GREEN}/summary{Style.RESET_ALL} - Show session summary")
        print(f"  {Fore.GREEN}/quit{Style.RESET_ALL}    - End session and exit")
        print(f"  {Fore.GREEN}/exit{Style.RESET_ALL}    - Same as /quit")
        print()
    
    def format_emotion(self, emotion: str) -> str:
        """Format emotion with color"""
        emotion_colors = {
            "excited": Fore.YELLOW,
            "happy": Fore.GREEN,
            "neutral": Fore.WHITE,
            "frustrated": Fore.RED,
            "tired": Fore.BLUE,
            "sad": Fore.CYAN
        }
        color = emotion_colors.get(emotion, Fore.WHITE)
        return f"{color}[{emotion}]{Style.RESET_ALL}"
    
    def print_summary(self):
        """Print session summary"""
        if not self.agent:
            print(f"{Fore.RED}No active session!{Style.RESET_ALL}")
            return
        
        summary = self.agent.get_summary()
        print(f"\n{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 Session Summary:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}")
        print(f"Session ID: {summary['session_id'][:8]}...")
        print(f"Duration: {summary['duration_minutes']:.1f} minutes")
        print(f"Messages: {summary['messages_count']}")
        print(f"Language Level: {Fore.GREEN}{summary['current_level']}{Style.RESET_ALL}")
        print(f"Current Emotion: {self.format_emotion(summary['current_emotion'])}")
        print(f"Emotion Trend: {summary['emotion_trend']}")
        print(f"Words Learned: {Fore.YELLOW}{summary['words_learned']}{Style.RESET_ALL}")
        print(f"Total Sessions: {summary['total_sessions']}")
        print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}\n")
    
    def start_session(self, session_id: Optional[str] = None):
        """Start a new session"""
        self.session_id = session_id or str(uuid.uuid4())
        print(f"{Fore.GREEN}Starting new session...{Style.RESET_ALL}")
        
        try:
            self.agent = SimpleTeachingAgent(
                session_id=self.session_id,
                api_key=self.api_key,
                base_url=self.base_url,
                model_name=self.model_name
            )
            print(f"{Fore.GREEN}Session started! (ID: {self.session_id[:8]}...){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Type '/help' for commands or just start chatting!{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{Fore.RED}Error starting session: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
    
    def run(self):
        """Run the CLI interface"""
        self.print_welcome()
        
        # Ask if user wants to continue existing session
        print(f"{Fore.CYAN}Do you want to:{Style.RESET_ALL}")
        print(f"  1. Start a {Fore.GREEN}new session{Style.RESET_ALL}")
        print(f"  2. Continue an {Fore.YELLOW}existing session{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.CYAN}Enter choice (1 or 2): {Style.RESET_ALL}").strip()
        
        if choice == "2":
            session_id = input(f"{Fore.CYAN}Enter session ID (or press Enter to start new): {Style.RESET_ALL}").strip()
            if session_id:
                self.start_session(session_id)
            else:
                self.start_session()
        else:
            self.start_session()
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input(f"\n{Fore.BLUE}You: {Style.RESET_ALL}").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    command = user_input.lower()
                    
                    if command in ['/quit', '/exit']:
                        farewell = self.agent.end()
                        print(f"\n{Fore.MAGENTA}Xiao Lin: {Style.RESET_ALL}{farewell}")
                        print(f"\n{Fore.CYAN}Thanks for learning with me! 再见! 👋{Style.RESET_ALL}\n")
                        break
                    
                    elif command == '/help':
                        self.print_help()
                        continue
                    
                    elif command == '/summary':
                        self.print_summary()
                        continue
                    
                    elif command == '/new':
                        if self.agent:
                            farewell = self.agent.end()
                            print(f"\n{Fore.MAGENTA}Xiao Lin: {Style.RESET_ALL}{farewell}")
                        self.start_session()
                        continue
                    
                    else:
                        print(f"{Fore.RED}Unknown command: {user_input}{Style.RESET_ALL}")
                        print(f"Type {Fore.GREEN}/help{Style.RESET_ALL} for available commands.")
                        continue
                
                # Process chat message
                print(f"\n{Fore.MAGENTA}Xiao Lin: {Style.RESET_ALL}", end="")
                response = self.agent.chat(user_input)
                
                # Format response with colors for Chinese words
                formatted_response = response
                # Highlight Chinese characters
                import re
                chinese_pattern = r'[\u4e00-\u9fff]+'
                formatted_response = re.sub(
                    chinese_pattern,
                    lambda m: f"{Fore.YELLOW}{m.group()}{Style.RESET_ALL}",
                    formatted_response
                )
                print(formatted_response)
                
            except KeyboardInterrupt:
                print(f"\n\n{Fore.YELLOW}Interrupted! Type '/quit' to exit properly.{Style.RESET_ALL}")
                continue
            
            except Exception as e:
                print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Let's try again!{Style.RESET_ALL}")
                continue


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Chinese Teaching Agent CLI - A fun way to learn Chinese!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_teaching_agent.py --api-key YOUR_API_KEY
  python cli_teaching_agent.py --api-key YOUR_API_KEY --model gpt-4
  python cli_teaching_agent.py --api-key YOUR_API_KEY --base-url https://api.openai.com/v1
        """
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)",
        default=os.getenv("OPENAI_API_KEY")
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        help="Custom base URL for OpenAI API",
        default=os.getenv("OPENAI_BASE_URL")
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (default: gpt-3.5-turbo)",
        default="gpt-3.5-turbo"
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not args.api_key:
        print(f"{Fore.RED}Error: OpenAI API key is required!{Style.RESET_ALL}")
        print(f"Set it via --api-key argument or OPENAI_API_KEY environment variable.")
        sys.exit(1)
    
    # Create and run CLI
    cli = TeachingAgentCLI(
        api_key=args.api_key,
        base_url=args.base_url,
        model_name=args.model
    )
    
    try:
        cli.run()
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
