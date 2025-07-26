"""
프로젝트 그룹화 시키는 클래스
"""
class ProjectGroupManager:
    
    """
    프로젝트별로 라인을 공유하는 프로젝트 그룹화
    """
    @staticmethod
    def create_project_groups(line_available_df) :
        project_groups = {}
        
        if 'Project' in line_available_df.columns :
            line_available_df = line_available_df.set_index('Project')
        
        line_to_projects = {}

        for line in line_available_df.columns :
            projects_using_line = []
            for project in line_available_df.index:
                if line_available_df.loc[project, line] == 1 :
                    projects_using_line.append(project)
            
            if len(projects_using_line) > 1 :
                line_to_projects[line] = projects_using_line

        grouped_projects = set()
        group_id = 1

        for line, projects in line_to_projects.items() :
            ungrouped_projects = [p for p in projects if p not in grouped_projects]

            if len(ungrouped_projects) > 1 :
                project_groups[f'Group{group_id:02d}'] = ungrouped_projects
                grouped_projects.update(ungrouped_projects)
                group_id += 1

        all_projects = set(line_available_df.index)
        single_projects = all_projects - grouped_projects

        for project in single_projects :
            project_groups[f'Group{group_id:02d}'] = [project]
            group_id += 1

        return project_groups
    
    """
    그룹에 속한 프로젝트들이 사용하는 라인 찾는 함수
    """
    @staticmethod
    def get_group_lines(group_projects, line_available_df) :
        used_lines = set()
        
        if 'Project' in line_available_df.columns :
            line_available_df = line_available_df.set_index('Project')
        
        for project in group_projects :
            for col in line_available_df.columns :
                if line_available_df.loc[project, col] == 1 :
                    used_lines.add(col)
        
        return used_lines
    
    """
    특정 프로젝트가 사용하는 라인 찾기
    """
    @staticmethod
    def get_project_lines(project, line_available_df):
        project_lines = []
        
        if 'Project' in line_available_df.columns:
            line_available_df = line_available_df.set_index('Project')
        
        for col in line_available_df.columns:
            if line_available_df.loc[project, col] == 1:
                project_lines.append(col)
        return project_lines
    
    """
    라인 공유 분석
    """
    @staticmethod
    def get_shared_lines(group_projects, line_available_df) :
        if 'Project' in line_available_df.columns :
            line_available_df = line_available_df.set_index('Project')

        shared_lines = []

        for line in line_available_df.columns :
            projects_using_line = 0

            for project in group_projects :
                if line_available_df.loc[project, line] == 1 :
                    projects_using_line += 1

            if projects_using_line > 1 :
                shared_lines.append(line)

        return shared_lines