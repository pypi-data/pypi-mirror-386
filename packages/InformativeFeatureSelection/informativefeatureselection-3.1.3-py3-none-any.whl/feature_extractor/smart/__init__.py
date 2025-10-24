import os


try:
    import segment_anything
    from .SegmentAnything import SegmentAnythingModel
    from .SmartMINDI import SmartMINDI
    
    print("[smart] dependencies are found, checking weights")
    
    from pathlib import Path
    dirpath = Path(__file__).parent.absolute()
    
    if not os.path.exists(os.path.join(dirpath, "weights", "sam_vit_h_4b8939.pth")):
        print("Weights have not been found, trying to download")
        import requests
        
        url = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth"
        os.makedirs(os.path.join(dirpath, "weights"), exist_ok=True)
        response = requests.get(url, stream=True)
        with open(os.path.join(dirpath, "weights", "sam_vit_h_4b8939.pth"), "wb") as f:
            f.write(response.content)
    else:
        print("Weights are found, OK")
        
        
except ImportError as e:
    print(e, ': not found. Consider installing with [smart]')