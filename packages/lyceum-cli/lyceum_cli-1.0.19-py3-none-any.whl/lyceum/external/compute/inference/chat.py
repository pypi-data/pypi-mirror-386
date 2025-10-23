"""
Synchronous inference commands for chat/completion
"""

from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
import json

from ....shared.config import config

console = Console()

# Import generated client modules
# We'll use direct HTTP calls since the sync inference models aren't generated yet

chat_app = typer.Typer(name="chat", help="Synchronous inference commands")


@chat_app.command("send")
def send_message(
    message: str = typer.Argument(..., help="Message to send to the model"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model to use for inference"),
    max_tokens: int = typer.Option(1000, "--max-tokens", help="Maximum tokens in response"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Temperature (0.0-2.0)"),
    system_prompt: Optional[str] = typer.Option(None, "--system", "-s", help="System prompt"),
):
    """Send a message to an AI model and get a response"""
    try:
        client = config.get_client()
        
        # Create the sync request payload directly
        sync_request = {
            "model_id": model,
            "input": {
                "text": message,
                "parameters": {"system_prompt": system_prompt} if system_prompt else {}
            },
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "stream": False
        }
        
        console.print(f"[dim]🤖 Sending message to {model}...[/dim]")
        
        # Make the API call using httpx directly (since we don't have generated client for sync inference yet)
        import httpx
        
        url = f"{config.base_url}/api/v2/external/sync/"
        headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
        
        with httpx.Client() as http_client:
            response = http_client.post(
                url,
                json=sync_request,
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                console.print(f"[green]✅ Response from {model}:[/green]")
                console.print(f"[cyan]{result['output']}[/cyan]")
                
                # Show usage stats
                if 'usage' in result:
                    usage = result['usage']
                    console.print(f"[dim]📊 Tokens: {usage.get('total_tokens', 0)} | "
                                f"Latency: {result.get('latency_ms', 0)}ms | "
                                f"Cost: ${result.get('cost', 0):.4f}[/dim]")
                
            elif response.status_code == 503:
                console.print(f"[red]❌ Model {model} is not running. Please contact support to start the model.[/red]")
                raise typer.Exit(1)
            else:
                console.print(f"[red]❌ Error: HTTP {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@chat_app.command("models")  
def list_models():
    """List available models for inference"""
    try:
        client = config.get_client()
        
        # Make API call to get available models
        import httpx
        
        url = f"{config.base_url}/api/v2/external/models/"
        headers = {"Authorization": f"Bearer {config.api_key}"}
        
        with httpx.Client() as http_client:
            response = http_client.get(url, headers=headers, timeout=10.0)
            
            if response.status_code == 200:
                models = response.json()
                
                if models:
                    # Create a table
                    table = Table(title="Available AI Models")
                    table.add_column("Model", style="cyan", no_wrap=True)
                    table.add_column("Type", style="magenta")
                    table.add_column("Status", justify="center")
                    table.add_column("Price/1K tokens", justify="right", style="green")
                    
                    # Sort models: running first, then by type, then by name
                    sorted_models = sorted(models, key=lambda m: (
                        not m.get('available', False),  # Running models first
                        m.get('type', 'text'),          # Then by type
                        m.get('model_id', '')           # Then by name
                    ))
                    
                    for model in sorted_models:
                        # Status with emoji
                        status = "🟢 Running" if model.get('available') else "🔴 Stopped"
                        
                        # Model type with emoji
                        model_type = model.get('type', 'text')
                        type_emoji = {
                            'text': 'Text',
                            'image': 'Image', 
                            'audio': 'Audio',
                            'multimodal': 'Multi',
                            'embedding': 'Embed'
                        }.get(model_type, f'❓ {model_type.title()}')
                        
                        # Provider
                        provider = model.get('provider', 'unknown').title()
                        
                        # Price
                        price = model.get('price_per_1k_tokens', 0)
                        price_str = f"${price:.4f}" if price > 0 else "Free"
                        
                        table.add_row(
                            model.get('model_id', 'Unknown'),
                            type_emoji,
                            status,
                            price_str
                        )
                    
                    console.print(table)
                    
                    # Show summary
                    running_count = sum(1 for m in models if m.get('available'))
                    total_count = len(models)
                    console.print(f"\n[dim]📊 {running_count}/{total_count} models running[/dim]")
                    
                else:
                    console.print("[yellow]No models are currently available[/yellow]")
            else:
                console.print(f"[red]❌ Error: HTTP {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@chat_app.command("image")
def analyze_image(
    image_source: str = typer.Argument(..., help="Image URL or path to base64 file"),
    prompt: str = typer.Option("What do you see in this image?", "--prompt", "-p", help="Question about the image"),
    model: str = typer.Option("paddleocr-vl", "--model", "-m", help="Vision model to use"),
    base64: bool = typer.Option(False, "--base64", "-b", help="Treat image_source as path to base64 file"),
):
    """Analyze an image with AI vision models"""
    try:
        client = config.get_client()

        # Prepare image data
        image_url = None
        image_data = None

        if base64:
            # Read base64 from file
            from pathlib import Path
            base64_path = Path(image_source)
            if not base64_path.exists():
                console.print(f"[red]❌ File not found: {image_source}[/red]")
                raise typer.Exit(1)

            with open(base64_path, 'r') as f:
                image_data = f.read().strip()

            console.print(f"[dim]📄 Read base64 image from {image_source} ({len(image_data)} chars)[/dim]")
        else:
            # Use as URL
            image_url = image_source

        # Create request payload for image analysis
        sync_request = {
            "model_id": model,
            "input": {
                "text": prompt,
            },
            "max_tokens": 1000,
            "temperature": 0.7
        }

        # Add image data
        if image_data:
            sync_request["input"]["image_data"] = image_data
        else:
            sync_request["input"]["image_url"] = image_url
        
        console.print(f"[dim]👁️  Analyzing image with {model}...[/dim]")
        
        import httpx
        
        url = f"{config.base_url}/api/v2/external/sync/"
        headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}
        
        with httpx.Client() as http_client:
            response = http_client.post(
                url,
                json=sync_request,
                headers=headers,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                console.print(f"[green]✅ Image Analysis:[/green]")
                console.print(f"[cyan]{result['output']}[/cyan]")
                
            elif response.status_code == 503:
                console.print(f"[red]❌ Vision model {model} is not running.[/red]")
                raise typer.Exit(1)
            else:
                console.print(f"[red]❌ Error: HTTP {response.status_code}[/red]")
                console.print(f"[red]{response.text}[/red]")
                raise typer.Exit(1)
                
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)