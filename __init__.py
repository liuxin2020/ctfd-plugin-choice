from flask import Blueprint, session
import random
from CTFd.models import (
    db,
    Solves,
    Fails,
    Flags,
    Challenges,
    ChallengeFiles,
    Tags,
    Hints,
)
from CTFd.plugins.flags import FlagException, get_flag_class
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.migrations import upgrade
from CTFd.utils.user import get_current_user, get_ip
from CTFd.utils.modes import get_model

class ChoiceChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "choice"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id",ondelete="CASCADE"), primary_key=True
    )
    flagchoose = db.Column(db.Text)
    
class ChoiceValueChallenge(BaseChallenge):
    id = "choice"  # Unique identifier used to register challenges
    name = "choice"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/ctfd-plugin-choice/assets/create.html",
        "update": "/plugins/ctfd-plugin-choice/assets/update.html",
        "view": "/plugins/ctfd-plugin-choice/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/ctfd-plugin-choice/assets/create.js",
        "update": "/plugins/ctfd-plugin-choice/assets/update.js",
        "view": "/plugins/ctfd-plugin-choice/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/ctfd-plugin-choice/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "choice",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = ChoiceChallenge

    

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.
        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = ChoiceChallenge.query.filter_by(id=challenge.id).first()

        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "description": challenge.description,
            "flagchoose": challenge.flagchoose,
            "connection_info": challenge.connection_info,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }

        return data
    @staticmethod
    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.
        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        ChoiceChallenge.query.filter_by(id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        db.session.commit()
        
def load(app):
    upgrade()
    CHALLENGE_CLASSES["choice"] = ChoiceValueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/ctfd-plugin-choice/assets/"
    )