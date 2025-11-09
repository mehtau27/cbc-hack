from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from pathlib import Path
from datetime import datetime
import json

from services.pose_extraction_service import PoseExtractionService
from services.comparison_service import ComparisonService
from services.feedback_service import FeedbackService

app = FastAPI(title="Dance Choreography Comparison System")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("uploads")
REPORTS_DIR = Path("reports")
UPLOAD_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Initialize services
pose_service = PoseExtractionService()
comparison_service = ComparisonService()
feedback_service = FeedbackService()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main web interface"""
    with open("static/index.html", "r") as f:
        return f.read()


@app.post("/upload-example")
async def upload_example(file: UploadFile = File(...)):
    """Upload example choreography video"""
    try:
        # Validate file type
        allowed_extensions = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}"
            )

        # Save file
        file_path = UPLOAD_DIR / f"example_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse({
            "message": "Example video uploaded successfully",
            "filename": file.filename,
            "file_path": str(file_path)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-assignment")
async def upload_assignment(file: UploadFile = File(...)):
    """Upload student assignment video"""
    try:
        allowed_extensions = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported"
            )

        file_path = UPLOAD_DIR / f"assignment_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse({
            "message": "Assignment video uploaded successfully",
            "filename": file.filename,
            "file_path": str(file_path)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-poses")
async def extract_poses(
    filename: str,
    video_type: str,  # "example" or "assignment"
    focus_areas: str = None  # Comma-separated list
):
    """Extract pose data from uploaded video"""
    try:
        file_path = UPLOAD_DIR / f"{video_type}_{filename}"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Parse focus areas
        focus_list = None
        if focus_areas:
            focus_list = [area.strip() for area in focus_areas.split(",")]

        # Extract poses
        pose_data = pose_service.extract_poses_from_video(
            str(file_path),
            focus_areas=focus_list
        )

        # Save pose data
        pose_file = UPLOAD_DIR / f"{video_type}_{filename}_poses.json"
        pose_service.save_pose_data(pose_data, str(pose_file))

        return JSONResponse({
            "message": "Pose extraction complete",
            "total_frames": pose_data['total_frames'],
            "duration": pose_data['duration'],
            "fps": pose_data['fps'],
            "pose_file": str(pose_file)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
async def compare_videos(
    example_filename: str,
    assignment_filename: str,
    focus_areas: str = None,
    student_name: str = "Student"
):
    """Compare assignment video to example video"""
    try:
        import traceback
        # Check if pose data already exists, otherwise extract
        example_pose_file = UPLOAD_DIR / f"example_{example_filename}_poses.json"
        assignment_pose_file = UPLOAD_DIR / f"assignment_{assignment_filename}_poses.json"

        focus_list = None
        if focus_areas:
            focus_list = [area.strip() for area in focus_areas.split(",")]

        # Extract poses if not already done
        if not example_pose_file.exists():
            example_video = UPLOAD_DIR / f"example_{example_filename}"
            example_pose_data = pose_service.extract_poses_from_video(
                str(example_video),
                focus_areas=focus_list
            )
            pose_service.save_pose_data(example_pose_data, str(example_pose_file))
        else:
            with open(example_pose_file, 'r') as f:
                example_pose_data = json.load(f)

        if not assignment_pose_file.exists():
            assignment_video = UPLOAD_DIR / f"assignment_{assignment_filename}"
            assignment_pose_data = pose_service.extract_poses_from_video(
                str(assignment_video),
                focus_areas=focus_list
            )
            pose_service.save_pose_data(assignment_pose_data, str(assignment_pose_file))
        else:
            with open(assignment_pose_file, 'r') as f:
                assignment_pose_data = json.load(f)

        # Compare videos
        comparison_result = comparison_service.compare_videos(
            example_pose_data,
            assignment_pose_data,
            focus_areas=focus_list
        )

        # Generate AI feedback
        ai_feedback = feedback_service.generate_enhanced_feedback(comparison_result)

        # Create comprehensive result
        result = {
            **comparison_result,
            'ai_feedback': ai_feedback,
            'student_name': student_name,
            'timestamp': datetime.now().isoformat()
        }

        # Save report
        report_filename = f"report_{student_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = REPORTS_DIR / report_filename

        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2)

        result['report_path'] = str(report_path)

        return JSONResponse(result)

    except Exception as e:
        import traceback
        print(f"ERROR in compare_videos: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports")
async def list_reports():
    """List all saved comparison reports"""
    try:
        reports = []
        for report_file in REPORTS_DIR.glob("*.json"):
            try:
                with open(report_file, 'r') as f:
                    data = json.load(f)
                    reports.append({
                        'filename': report_file.name,
                        'student_name': data.get('student_name', 'Unknown'),
                        'timestamp': data.get('timestamp', ''),
                        'overall_similarity': data.get('overall_similarity', 0),
                        'path': str(report_file)
                    })
            except Exception as e:
                print(f"Error reading report {report_file}: {e}")
                continue

        # Sort by timestamp, newest first (handle empty timestamps)
        reports.sort(key=lambda x: x['timestamp'] or '', reverse=True)

        return JSONResponse({'reports': reports})

    except Exception as e:
        import traceback
        print(f"Error in list_reports: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/{filename}")
async def get_report(filename: str):
    """Get a specific report"""
    try:
        report_path = REPORTS_DIR / filename

        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        with open(report_path, 'r') as f:
            report = json.load(f)

        return JSONResponse(report)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/reports/{filename}")
async def delete_report(filename: str):
    """Delete a report"""
    try:
        report_path = REPORTS_DIR / filename

        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        os.remove(report_path)

        return JSONResponse({"message": "Report deleted successfully"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
